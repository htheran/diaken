from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms_sequential import SequentialPlaybookForm
from playbooks.models import Playbook
from inventory.models import Environment, Group, Host
from app_settings.models import GlobalSetting
import ansible_runner
import tempfile
import os

from django.core.paginator import Paginator

@login_required
def sequential_history(request):
    from history.models import History
    sequential_list = History.objects.filter(execution_type='sequential').order_by('-date')
    paginator = Paginator(sequential_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'history/sequential_history_list.html', {'page_obj': page_obj})

def deploy_sequential(request):
    results = []
    if request.method == 'POST':
        form = SequentialPlaybookForm(request.POST)
        if form.is_valid():
            environment = form.cleaned_data['environment']
            group = form.cleaned_data['group']
            host = form.cleaned_data['host']
            playbooks = list(form.cleaned_data['playbooks'])
            playbooks_order = form.cleaned_data.get('playbooks_order')
            if playbooks_order:
                id_order = [int(i) for i in playbooks_order.split(',') if i.isdigit()]
                playbooks = sorted(playbooks, key=lambda pb: id_order.index(pb.id) if pb.id in id_order else 999)
            # Ejecutar playbooks en orden
            import re
            from history.models import History
            for pb in playbooks:
                # Preparar inventario temporal
                inventory_path = generate_temporary_inventory(group_id=group.id if group else None, host_id=host.id if host else None)
                extravars = get_all_settings_as_dict()
                extravars['target_host'] = host.name

                # Reemplazo de hosts: target_host por hosts: <host.name> (igual que en deploy_to_host)
                with open(pb.file.path, 'r') as original_pb:
                    pb_content = original_pb.read()
                pb_content = pb_content.replace('hosts: target_host', f'hosts: {host.name}')
                with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.yml') as temp_pb:
                    temp_pb.write(pb_content)
                    temp_pb_path = temp_pb.name

                r = ansible_runner.run(
                    private_data_dir=tempfile.gettempdir(),
                    playbook=temp_pb_path,
                    inventory=inventory_path,
                    extravars=extravars
                )
                output = r.stdout.read() if hasattr(r.stdout, 'read') else str(r)

                # Mejorar lógica: buscar el bloque PLAY RECAP y analizar el último resumen
                clean_output = re.sub(r'\x1B\[[0-?]*[ -/]*[@-~]', '', output)
                import re
                play_recap_blocks = re.findall(r'PLAY RECAP[\s\S]+?(ok=\d+\s+changed=\d+\s+unreachable=\d+\s+failed=\d+)', clean_output)
                last_summary = None
                if play_recap_blocks:
                    # Tomar el último resumen encontrado
                    last_block = play_recap_blocks[-1]
                    match = re.search(r'ok=(\d+)\s+changed=(\d+)\s+unreachable=(\d+)\s+failed=(\d+)', last_block)
                    if match:
                        ok, changed, unreachable, failed = map(int, match.groups())
                        if failed == 0 and unreachable == 0:
                            status = 'successful'
                            resumen = '✅ Ejecución exitosa\n' if changed == 0 else '✅ Ejecución exitosa (se realizaron cambios)\n'
                        else:
                            status = 'failed'
                            resumen = '❌ Ejecución fallida\n'
                        last_summary = resumen
                if last_summary is None:
                    # Fallback: buscar cualquier resumen en todo el output
                    match = re.search(r'ok=(\d+)\s+changed=(\d+)\s+unreachable=(\d+)\s+failed=(\d+)', clean_output)
                    if match:
                        ok, changed, unreachable, failed = map(int, match.groups())
                        if failed == 0 and unreachable == 0:
                            status = 'successful'
                            resumen = '✅ Ejecución exitosa\n' if changed == 0 else '✅ Ejecución exitosa (se realizaron cambios)\n'
                        else:
                            status = 'failed'
                            resumen = '❌ Ejecución fallida\n'
                    else:
                        status = 'failed'
                        resumen = '❌ Ejecución fallida (no se pudo interpretar el resultado)\n'
                else:
                    resumen = last_summary
                history_output = resumen + clean_output

                # Guardar historial de ejecución secuencial
                History.objects.create(
                    playbook=pb,
                    user=request.user,
                    host=host,
                    group=group,
                    environment=environment,  # Agregar el ambiente al historial
                    status=status,
                    output=history_output,
                    execution_type='sequential'
                )

                results.append({'playbook': pb.name, 'status': status, 'rc': r.rc, 'output': history_output})
                os.remove(inventory_path)
                os.remove(temp_pb_path)

        # Mostrar modal igual que en deploy_to_host
        return redirect(f'{request.path}?show_result_modal=true')
    else:
        form = SequentialPlaybookForm()
    return render(request, 'deploy/deploy_sequential.html', {'form': form, 'results': results})

def generate_temporary_inventory(group_id=None, host_id=None):
    import os
    from django.shortcuts import get_object_or_404
    import tempfile
    from inventory.models import Host, Group
    with tempfile.NamedTemporaryFile(delete=False, mode='w', dir='/tmp') as inventory_file:
        inventory_path = inventory_file.name
        inventory_file.write("[all:vars]\n\n")
        if host_id:
            host = get_object_or_404(Host, id=host_id)
            private_key_path = ''
            if hasattr(host, 'deployment_credential') and host.deployment_credential and hasattr(host.deployment_credential, 'ssh_private_key_encrypted') and host.deployment_credential.ssh_private_key_encrypted:
                ssh_key = host.deployment_credential.get_ssh_private_key()
                key_bytes = (ssh_key.strip() + '\n').encode('utf-8')
                key_file = tempfile.NamedTemporaryFile(delete=False, mode='wb', dir='/tmp')
                key_file.write(key_bytes)
                key_file.close()
                os.chmod(key_file.name, 0o600)
                private_key_path = key_file.name
            inventory_file.write(f"[target_host]\n")
            user = host.deployment_credential.user if hasattr(host, 'deployment_credential') and host.deployment_credential and hasattr(host.deployment_credential, 'user') else 'root'
            ssh_key_valid = bool(private_key_path and os.path.exists(private_key_path) and os.path.getsize(private_key_path) > 100)
            line = (
                f"{host.name} ansible_host={host.ip} ansible_python_interpreter={host.ansible_python_interpreter}"
                f" ansible_user={user}"
                f" ansible_become={'yes' if getattr(host, 'ansible_become', False) else 'no'}"
                f" ansible_become_method={getattr(host, 'ansible_become_method', '') if getattr(host, 'ansible_become_method', '') else ''}"
                f" ansible_ssh_common_args='-o StrictHostKeyChecking=no'"
            )
            if ssh_key_valid:
                line += f" ansible_ssh_private_key_file={private_key_path}"
            line += "\n"
            inventory_file.write(line)
        elif group_id:
            group = Group.objects.get(id=group_id)
            inventory_file.write(f'[{group.name}]\n')
            for host in group.host_set.all():
                inventory_file.write(f'{host.name}\n')
    return inventory_path

def get_all_settings_as_dict():
    settings = GlobalSetting.objects.all()
    settings_dict = {}
    for setting in settings:
        try:
            import json
            settings_dict[setting.key] = json.loads(setting.value)
        except Exception:
            settings_dict[setting.key] = setting.value
    return settings_dict
