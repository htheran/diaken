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

@login_required
def schedule_to_host(request):
    if request.method == 'POST':
        form = ScheduledDeploymentHostForm(request.POST)
        if form.is_valid():
            sched = form.save(commit=False)
            sched.user = request.user
            sched.deploy_type = 'host'
            now = timezone.localtime(timezone.now())
            sched_time = timezone.localtime(sched.scheduled_time)
            delta_seconds = (sched_time - now).total_seconds()
            print(f'[DEBUG] schedule_to_host | scheduled_time: {sched_time} | now: {now} | delta_seconds: {delta_seconds} | ejecutar_inmediato: {delta_seconds <= 60}')
            from django.contrib import messages
            if delta_seconds <= 60:
                sched.status = 'running'
                sched.save()
                try:
                    inventory_path = generate_temporary_inventory(host_id=sched.host.id)
                    pb_path = Command.prepare_playbook_static(sched.playbook.file.path, 'hosts: target_host', f'hosts: {sched.host.name}')
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
