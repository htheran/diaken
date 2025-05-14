from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms_scheduled import ScheduledDeploymentHostForm, ScheduledDeploymentGroupForm
from .models import ScheduledDeployment
from django.utils import timezone
from .models import ScheduledDeployment

from django.utils import timezone
import ansible_runner
import os
from deploy.views import generate_temporary_inventory

def _ensure_critical_variables(extravars):
    """Asegura que todas las variables críticas estén definidas"""
    critical_vars = {
        'server_root': '/opt/www/sites',
        'log_root': '/var/log/httpd',
        'http_port': '80',
        'https_port': '443',
        'domain': 'example.com'
    }
    
    for key, default_value in critical_vars.items():
        if key not in extravars or not extravars[key]:
            print(f'ADVERTENCIA: Variable {key} no definida, usando valor predeterminado: {default_value}')
            extravars[key] = default_value

@login_required
def schedule_to_host(request):
    if request.method == 'POST':
        print(f"[DEBUG] POST data: {request.POST}")
        form = ScheduledDeploymentHostForm(request.POST)
        print(f"[DEBUG] Form is valid: {form.is_valid()}")
        if form.is_valid():
            # Obtener los campos del formulario
            environment = form.cleaned_data.get('environment')
            group = form.cleaned_data.get('group')
            host = form.cleaned_data.get('host')
            playbook = form.cleaned_data.get('playbook')
            scheduled_time = form.cleaned_data.get('scheduled_time')
            
            print(f"[DEBUG] Datos del formulario: environment={environment}, group={group}, host={host}, playbook={playbook}, scheduled_time={scheduled_time}")
            
            # Validar que el host pertenezca al grupo seleccionado
            if host.group.id != group.id:
                from django.contrib import messages
                messages.error(request, f'El host {host.name} no pertenece al grupo {group.name}')
                return redirect('schedule_to_host')
            
            # Crear el objeto de tarea programada
            sched = ScheduledDeployment()
            sched.user = request.user
            sched.deploy_type = 'host'
            sched.host = host
            sched.playbook = playbook
            sched.scheduled_time = scheduled_time
            
            print(f"[DEBUG] Objeto de tarea programada: host={sched.host}, playbook={sched.playbook}, scheduled_time={sched.scheduled_time}")
            
            now = timezone.localtime(timezone.now())
            sched_time = timezone.localtime(sched.scheduled_time)
            delta_seconds = (sched_time - now).total_seconds()
            print(f'[DEBUG] schedule_to_host | scheduled_time: {sched_time} | now: {now} | delta_seconds: {delta_seconds} | ejecutar_inmediato: {delta_seconds <= 60}')
            from django.contrib import messages
            
            # Determinar si se debe ejecutar inmediatamente o programar para el futuro
            if delta_seconds <= 60:
                # Ejecutar inmediatamente
                sched.status = 'running'
                sched.save()
                try:
                    # Obtener todas las variables de configuración global
                    from deploy.views import get_all_settings_as_dict
                    extravars = get_all_settings_as_dict()
                    
                    # Asegurar que las variables críticas estén definidas
                    _ensure_critical_variables(extravars)
                    
                    # Añadir target_host como variable para las plantillas
                    extravars['target_host'] = sched.host.name
                    
                    print(f"[DEBUG] Variables de configuración: {extravars}")
                    
                    inventory_path = generate_temporary_inventory(host_id=sched.host.id)
                    pb_path = Command.prepare_playbook_static(sched.playbook.file.path, 'hosts: target_host', f'hosts: {sched.host.name}')
                    result = ansible_runner.run(
                        private_data_dir='/opt/www',
                        playbook=pb_path,
                        inventory=inventory_path,
                        extravars=extravars
                    )
                    output = result.stdout.read()
                    sched.output = output
                    sched.status = 'successful' if result.rc == 0 else 'failed'
                    sched.executed_at = timezone.now()
                    os.remove(inventory_path)
                    os.remove(pb_path)
                    if sched.status == 'successful':
                        messages.success(request, 'La tarea se ejecutó inmediatamente y fue exitosa.')
                    else:
                        messages.warning(request, 'La tarea se ejecutó inmediatamente pero falló. Verifique el historial para más detalles.')
                except Exception as e:
                    import traceback
                    sched.status = 'failed'
                    sched.output = f'{str(e)}\nTRACEBACK:\n{traceback.format_exc()}'
                    sched.executed_at = timezone.now()
                    print(f'[ERROR] Scheduled deployment failed: {e}\n{traceback.format_exc()}')
                    messages.error(request, f'Ocurrió un error al ejecutar la tarea inmediatamente: {e}')
                sched.save()
            else:
                # Programar para el futuro
                sched.status = 'pending'
                sched.save()
                messages.success(request, 'La tarea ha sido programada correctamente para ejecución futura.')
            
            return redirect('scheduled_history')
        else:
            # Si el formulario no es válido, mostrar errores
            print(f"[DEBUG] Errores del formulario: {form.errors}")
            from django.contrib import messages
            messages.error(request, 'Por favor corrija los errores en el formulario.')
    else:
        form = ScheduledDeploymentHostForm()
    return render(request, 'deploy/schedule_to_host.html', {'form': form})

@login_required
def schedule_to_group(request):
    if request.method == 'POST':
        form = ScheduledDeploymentGroupForm(request.POST)
        if form.is_valid():
            sched = form.save(commit=False)
            sched.user = request.user
            sched.deploy_type = 'group'
            now = timezone.localtime(timezone.now())
            sched_time = timezone.localtime(sched.scheduled_time)
            delta_seconds = (sched_time - now).total_seconds()
            print(f'[DEBUG] schedule_to_group | scheduled_time: {sched_time} | now: {now} | delta_seconds: {delta_seconds} | ejecutar_inmediato: {delta_seconds <= 60}')
            from django.contrib import messages
            if delta_seconds <= 60:
                sched.status = 'running'
                sched.save()
                try:
                    inventory_path = generate_temporary_inventory(group_id=sched.group.id)
                    pb_path = Command.prepare_playbook_static(sched.playbook.file.path, 'hosts: target_group', f'hosts: {sched.group.name}')
                    result = ansible_runner.run(
                        private_data_dir='/opt/www',
                        playbook=pb_path,
                        inventory=inventory_path
                    )
                    output = result.stdout.read()
                    sched.output = output
                    sched.status = 'successful' if result.rc == 0 else 'failed'
                    sched.executed_at = timezone.now()
                    os.remove(inventory_path)
                    os.remove(pb_path)
                    if sched.status == 'successful':
                        messages.success(request, 'La tarea se ejecutó inmediatamente y fue exitosa.')
                    else:
                        messages.warning(request, 'La tarea se ejecutó inmediatamente pero falló. Verifique el historial para más detalles.')
                except Exception as e:
                    import traceback
                    sched.status = 'failed'
                    sched.output = f'{str(e)}\nTRACEBACK:\n{traceback.format_exc()}'
                    sched.executed_at = timezone.now()
                    print(f'[ERROR] Scheduled deployment failed: {e}\n{traceback.format_exc()}')
                    messages.error(request, f'Ocurrió un error al ejecutar la tarea inmediatamente: {e}')
                sched.save()
            else:
                sched.status = 'pending'
                sched.save()
                messages.info(request, 'La tarea fue agendada para ejecución futura.')
            return redirect('scheduled_history')
    else:
        form = ScheduledDeploymentGroupForm()
    return render(request, 'deploy/schedule_to_group.html', {'form': form})

# Método utilitario para preparar el playbook, igual que en el comando
class Command:
    @staticmethod
    def prepare_playbook_static(playbook_path, find_str, replace_str):
        import tempfile
        with open(playbook_path, 'r') as original_pb:
            pb_content = original_pb.read()
        pb_content = pb_content.replace(find_str, replace_str)
        pb_file = tempfile.NamedTemporaryFile(delete=False, mode='w', dir='/tmp', suffix='.yml')
        pb_file.write(pb_content)
        pb_file.close()
        return pb_file.name

def scheduled_history(request):
    scheduled_list = ScheduledDeployment.objects.all().order_by('-scheduled_time')
    return render(request, 'history/scheduled_history_list.html', {'scheduled_list': scheduled_list})


def api_scheduled_status(request):
    """Endpoint API para obtener el estado actual de las tareas programadas"""
    from django.http import JsonResponse
    
    # Obtener el parámetro de filtro por estado (si existe)
    status_filter = request.GET.get('status', None)
    
    # Filtrar las tareas programadas según el estado solicitado
    if status_filter:
        scheduled_list = ScheduledDeployment.objects.filter(status=status_filter).order_by('-scheduled_time')
    else:
        scheduled_list = ScheduledDeployment.objects.all().order_by('-scheduled_time')
    
    # Preparar los datos para la respuesta JSON
    tasks = []
    for sched in scheduled_list:
        task = {
            'id': sched.id,
            'status': sched.status,
            'status_html': get_status_html(sched.status),
            'output': sched.output,
            'output_html': get_output_html(sched)
        }
        tasks.append(task)
    
    return JsonResponse({'tasks': tasks})


def get_status_html(status):
    """Genera el HTML para mostrar el estado de una tarea programada"""
    if status == 'successful':
        return '<span class="badge badge-success"><i class="fas fa-check-circle"></i> Success</span>'
    elif status == 'failed':
        return '<span class="badge badge-danger"><i class="fas fa-times-circle"></i> Failed</span>'
    elif status == 'pending':
        return '<span class="badge badge-warning"><i class="fas fa-clock"></i> Pending</span>'
    elif status == 'running':
        return '<span class="badge badge-info"><i class="fas fa-spinner fa-spin"></i> Running</span>'
    else:
        return f'<span class="badge badge-secondary">{status}</span>'


def get_output_html(sched):
    """Genera el HTML para mostrar el output de una tarea programada"""
    if sched.output:
        truncated_output = sched.output[:80] + '...' if len(sched.output) > 80 else sched.output
        return f'<span style="white-space: pre-line;">{truncated_output}</span> <a href="#" data-toggle="modal" data-target="#outputModal{sched.id}">Ver todo</a>'
    else:
        return '<span class="text-muted">-</span>'
