from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from inventory.models import Host, Group, Environment
from playbooks.models import Playbook
from history.models import History
from app_settings.models import GlobalSetting
import ansible_runner
import logging
import os
import tempfile
import json

# Función auxiliar para obtener todas las variables de GlobalSetting
def get_all_settings_as_dict():
    """Obtiene todas las variables de GlobalSetting y las devuelve como un diccionario"""
    settings = GlobalSetting.objects.all()
    settings_dict = {}
    
    for setting in settings:
        # Intentar convertir a JSON si es posible (para manejar objetos complejos)
        try:
            settings_dict[setting.key] = json.loads(setting.value)
        except (json.JSONDecodeError, TypeError):
            # Si no es JSON válido, usar el valor como string
            settings_dict[setting.key] = setting.value
    
    return settings_dict

logger = logging.getLogger(__name__)

# Create your views here.

def generate_temporary_inventory(group_id=None, host_id=None):
    with tempfile.NamedTemporaryFile(delete=False, mode='w', dir='/tmp') as inventory_file:
        inventory_path = inventory_file.name

        # Configuración global para Ansible (sin ansible_connection=local para forzar conexión SSH)
        inventory_file.write("[all:vars]\n")
        inventory_file.write("\n")

        # Si se proporciona un grupo, escribe los hosts del grupo
        if group_id:
            group = get_object_or_404(Group, id=group_id)
            inventory_file.write(f'[{group.name}]\n')
            hosts = Host.objects.filter(group=group)
            for host in hosts:
                private_key_path = ''
                if host.deployment_credential and host.deployment_credential.ssh_private_key_encrypted:
                    ssh_key = host.deployment_credential.get_ssh_private_key()
                    key_bytes = (ssh_key.strip() + '\n').encode('utf-8')
                    key_file = tempfile.NamedTemporaryFile(delete=False, mode='wb', dir='/tmp')
                    key_file.write(key_bytes)
                    key_file.close()
                    os.chmod(key_file.name, 0o600)
                    private_key_path = key_file.name
                user = host.deployment_credential.user if host.deployment_credential and hasattr(host.deployment_credential, 'user') else 'root'
                ssh_key_valid = bool(private_key_path and os.path.exists(private_key_path) and os.path.getsize(private_key_path) > 100)
                line = (
                    f"{host.name} ansible_host={host.ip} ansible_python_interpreter={host.ansible_python_interpreter}"
                    f" ansible_user={user}"
                    f" ansible_become={'yes' if host.ansible_become else 'no'}"
                    f" ansible_become_method={host.ansible_become_method if host.ansible_become_method else ''}"
                    f" ansible_ssh_common_args='-o StrictHostKeyChecking=no'"
                )
                if ssh_key_valid:
                    line += f" ansible_ssh_private_key_file={private_key_path}"
                line += "\n"
                inventory_file.write(line)
        # Si se proporciona un host, escribe solo ese host
        elif host_id:
            host = get_object_or_404(Host, id=host_id)
            
            # Escribir configuración global
            inventory_file.write("[all:vars]\n")
            inventory_file.write("ansible_connection=ssh\n")
            inventory_file.write("ansible_port=22\n")
            inventory_file.write("ansible_ssh_common_args='-o StrictHostKeyChecking=no'\n\n")
            
            # Escribir grupo target_host
            inventory_file.write("[target_host]\n")
            
            if host.operating_system == 'Windows':
                # Configuración para Windows
                user = host.ansible_user or (host.deployment_credential.user if host.deployment_credential else 'Administrator')
                password = ''
                if host.deployment_credential and hasattr(host.deployment_credential, 'get_windows_password'):
                    password = host.deployment_credential.get_windows_password() or ''
                
                # Escribir host con configuración Windows
                inventory_file.write(f"{host.name} ")
                inventory_file.write(f"ansible_host={host.ip} ")
                inventory_file.write(f"ansible_user={user} ")
                if password:
                    inventory_file.write(f"ansible_password={password} ")
                inventory_file.write("ansible_shell_type=powershell\n")
                
            else:
                # Configuración para Linux/Unix con opciones de depuración
                user = host.ansible_user or (host.deployment_credential.user if host.deployment_credential else 'root')
                
                # Usar el nombre del host como identificador en el inventario
                inventory_file.write(f"{host.name} ")
                inventory_file.write(f"ansible_host={host.ip} ")
                inventory_file.write(f"ansible_user={user} ")
                
                # Configuración básica
                inventory_file.write(f"ansible_python_interpreter={host.ansible_python_interpreter} ")
                inventory_file.write(f"ansible_become={'yes' if host.ansible_become else 'no'} ")
                
                if host.ansible_become_method:
                    inventory_file.write(f"ansible_become_method={host.ansible_become_method} ")
                
                # Configuración de SSH para depuración
                inventory_file.write("ansible_ssh_common_args='-o StrictHostKeyChecking=no -o PreferredAuthentications=password,keyboard-interactive' ")
                
                # Permitir autenticación por contraseña para depuración
                inventory_file.write("ansible_ssh_pass='' ")
                inventory_file.write("ansible_ssh_extra_args='-v' ")
                
                inventory_file.write("\n")

    # Logging para depuración
    try:
        with open(inventory_path, 'r') as f:
            contenido = f.read()
        # logger.info(f"[DEPURACIÓN] Inventario temporal generado en: {inventory_path}\nContenido:\n{contenido}")
    except Exception as e:
        logger.error(f"[DEPURACIÓN] Error al leer el inventario temporal: {e}")
    return inventory_path


def get_ansible_status(output):
    import re
    clean_output = re.sub(r'\x1B\[[0-?]*[ -/]*[@-~]', '', output)
    match = re.search(r'ok=(\d+)\s+changed=(\d+)\s+unreachable=(\d+)\s+failed=(\d+)', clean_output)
    if match:
        ok, changed, unreachable, failed = map(int, match.groups())
        if failed == 0 and unreachable == 0:
            status = 'successful'
            if changed == 0:
                resumen = "✅ Ejecución exitosa\n"
            else:
                resumen = "✅ Ejecución exitosa (se realizaron cambios)\n"
        else:
            status = 'failed'
            resumen = "❌ Ejecución fallida\n"
    else:
        status = 'failed'
        resumen = "❌ Ejecución fallida (no se pudo interpretar el resultado)\n"
    return status, resumen + clean_output

def deploy_to_host(request):
    if request.method == 'POST':
        playbook_id = request.POST.get('playbook')
        host_id = request.POST.get('host')
        
        # Validar que los IDs no estén vacíos
        if not playbook_id:
            messages.error(request, 'Por favor, seleccione un playbook válido.')
            return redirect('deploy_to_host')
            
        if not host_id:
            messages.error(request, 'Por favor, seleccione un host válido.')
            return redirect('deploy_to_host')
            
        # Obtener los objetos
        try:
            playbook = Playbook.objects.get(id=playbook_id)
            host = Host.objects.get(id=host_id)
        except (Playbook.DoesNotExist, Host.DoesNotExist, ValueError) as e:
            messages.error(request, f'Error al obtener playbook o host: {str(e)}')
            return redirect('deploy_to_host')

        # print('DEBUG deploy_to_host: host_id recibido:', host_id)
        # print('DEBUG deploy_to_host: host seleccionado:', host.name)

        # Genera archivo de inventario temporal
        inventory_path = generate_temporary_inventory(host_id=host_id)
        with open(inventory_path, 'r') as f:
            pass  # No debug output; bloque requerido para evitar error de indentación

        # Obtener todas las variables de configuración automáticamente
        extravars = get_all_settings_as_dict()
        
        # Añadir target_host como variable para las plantillas
        extravars['target_host'] = host.name

        # Crear copia temporal del playbook sin modificar el target_host
        import tempfile
        with open(playbook.file.path, 'r') as original_pb:
            pb_content = original_pb.read()
        # No reemplazar el target_host, dejarlo como está
        with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.yml') as temp_pb:
            temp_pb.write(pb_content)
            temp_pb_path = temp_pb.name

        # Run Ansible playbook con archivo temporal modificado
        result = ansible_runner.run(
            private_data_dir='/opt/www',
            playbook=temp_pb_path,
            inventory=inventory_path,
            extravars=extravars
        )

        # Eliminar archivos temporales
        os.remove(inventory_path)
        os.remove(temp_pb_path)

        # Determinar status correctamente del output de Ansible
        import re
        output = result.stdout.read()

        # Nueva lógica de status universal (también para despliegue por grupo)
        clean_output = re.sub(r'\x1B\[[0-?]*[ -/]*[@-~]', '', output)
        match = re.search(r'ok=(\d+)\s+changed=(\d+)\s+unreachable=(\d+)\s+failed=(\d+)', clean_output)
        if match:
            ok, changed, unreachable, failed = map(int, match.groups())
            if failed == 0 and unreachable == 0:
                status = 'successful'
                if changed == 0:
                    resumen = "✅ Ejecución exitosa\n"
                else:
                    resumen = "✅ Ejecución exitosa (se realizaron cambios)\n"
            else:
                status = 'failed'
                resumen = "❌ Ejecución fallida\n"
        else:
            status = 'failed'
            resumen = "❌ Ejecución fallida (no se pudo interpretar el resultado)\n"
        output = resumen + clean_output

        # Save history with correct status
        History.objects.create(
            playbook=playbook,
            user=request.user,
            host=host,
            status=status,
            output=output,
            execution_type='manual'
        )
        # logger.info(result.stats)
        return redirect('deploy_success')
    else:
        playbooks = Playbook.objects.all()
        hosts = Host.objects.all()
        environments = Environment.objects.all()
        return render(request, 'deploy/deploy_to_host.html', {'playbooks': playbooks, 'hosts': hosts, 'environments': environments})


def deploy_to_group(request):
    if request.method == 'POST':
        playbook_id = request.POST.get('playbook')
        group_id = request.POST.get('group')
        environment_id = request.POST.get('environment')
        
        # Validar que los IDs no estén vacíos
        if not playbook_id:
            messages.error(request, 'Por favor, seleccione un playbook válido.')
            return redirect('deploy_to_group')
            
        if not group_id:
            messages.error(request, 'Por favor, seleccione un grupo válido.')
            return redirect('deploy_to_group')
            
        # Obtener los objetos
        try:
            playbook = Playbook.objects.get(id=playbook_id)
            group = Group.objects.get(id=group_id)
            environment = Environment.objects.get(id=environment_id) if environment_id else None
        except (Playbook.DoesNotExist, Group.DoesNotExist, Environment.DoesNotExist, ValueError) as e:
            messages.error(request, f'Error al obtener playbook, grupo o entorno: {str(e)}')
            return redirect('deploy_to_group')

        # Genera archivo de inventario temporal
        inventory_path = generate_temporary_inventory(group_id=group_id)

        # Obtener todas las variables de configuración automáticamente
        extravars = get_all_settings_as_dict()
        
        # Añadir target_group al diccionario de variables
        extravars['target_group'] = group.name
        
        # Añadir environment al diccionario de variables si existe
        if environment:
            extravars['environment'] = environment.name

        # Crear copia temporal del playbook con reemplazo de hosts: target_group
        import tempfile
        with open(playbook.file.path, 'r') as original_pb:
            pb_content = original_pb.read()
        pb_content = pb_content.replace('hosts: target_group', f'hosts: {group.name}')
        with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.yml') as temp_pb:
            temp_pb.write(pb_content)
            temp_pb_path = temp_pb.name

        # Run Ansible playbook con archivo temporal modificado
        result = ansible_runner.run(
            private_data_dir='/opt/www',
            playbook=temp_pb_path,
            inventory=inventory_path,
            extravars=extravars
        )

        # Eliminar archivos temporales
        os.remove(inventory_path)
        os.remove(temp_pb_path)

        output = result.stdout.read()
        status, output = get_ansible_status(output)

        # Save history
        history_entry = History.objects.create(
            playbook=playbook,
            user=request.user,
            group=group,
            status=status,
            output=output
        )
        
        # Guardar el ambiente en el historial si existe
        if environment:
            history_entry.environment = environment
            history_entry.save()
        logger.info(result.stats)
        return redirect('deploy_success')
    else:
        # Solo playbooks de tipo 'group'
        playbooks = Playbook.objects.filter(playbook_type='group')
        # Inicialmente no mostrar grupos hasta que se seleccione un ambiente
        groups = Group.objects.none()
        environments = Environment.objects.all()
        return render(request, 'deploy/deploy_to_group.html', {'playbooks': playbooks, 'groups': groups, 'environments': environments})

def deploy_success(request):
    # Redirigir a la página de despliegue con un parámetro para mostrar el modal
    from django.urls import reverse
    return redirect(reverse('deploy_to_host') + '?show_result_modal=true')

def api_groups(request):
    environment_id = request.GET.get('environment_id')
    groups = Group.objects.filter(environment_id=environment_id).values('id', 'name')
    return JsonResponse({'groups': list(groups)})


def api_hosts(request):
    group_id = request.GET.get('group_id')
    hosts = Host.objects.filter(group_id=group_id).values('id', 'name')
    return JsonResponse({'hosts': list(hosts)})
