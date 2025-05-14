from django.core.management.base import BaseCommand
from deploy.models import ScheduledDeployment
from django.utils import timezone
from playbooks.models import Playbook
from inventory.models import Host, Group
from django.contrib.auth.models import User
import ansible_runner
import os
import tempfile
import json
from deploy.views import generate_temporary_inventory

# Replicamos exactamente la misma función que funciona en views.py
def get_all_settings_as_dict():
    """Obtiene todas las variables de GlobalSetting y las devuelve como un diccionario"""
    from app_settings.models import GlobalSetting
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

class Command(BaseCommand):
    help = 'Run scheduled deployments that are pending and due'

    def handle(self, *args, **options):
        now = timezone.now()
        pending = ScheduledDeployment.objects.filter(status='pending', scheduled_time__lte=now)
        for sched in pending:
            self.stdout.write(f'Running scheduled deployment: {sched}')
            sched.status = 'running'
            sched.save()
            try:
                if sched.deploy_type == 'host' and sched.host:
                    # --- Lógica similar a deploy_to_host ---
                    inventory_path = generate_temporary_inventory(host_id=sched.host.id)
                    
                    # Obtener todas las variables de configuración automáticamente
                    # IMPORTANTE: Usamos la función local, no la importada
                    extravars = get_all_settings_as_dict()
                    self.stdout.write(f'EXTRAVARS ENVIADOS: {extravars}')
                    
                    # Crear copia temporal del playbook con reemplazo de hosts: target_host
                    pb_path = self.prepare_playbook(sched.playbook.file.path, 'hosts: target_host', f'hosts: {sched.host.name}')
                    
                    # Run Ansible playbook con archivo temporal modificado
                    result = ansible_runner.run(
                        private_data_dir='/opt/www',
                        playbook=pb_path,
                        inventory=inventory_path,
                        extravars=extravars
                    )
                    output = result.stdout.read()
                    sched.output = output
                    sched.status = 'successful' if result.rc == 0 else 'failed'
                    os.remove(inventory_path)
                    os.remove(pb_path)
                elif sched.deploy_type == 'group' and sched.group:
                    # --- Lógica similar a deploy_to_group ---
                    inventory_path = generate_temporary_inventory(group_id=sched.group.id)
                    
                    # Obtener todas las variables de configuración automáticamente
                    # IMPORTANTE: Usamos la función local, no la importada
                    extravars = get_all_settings_as_dict()
                    self.stdout.write(f'EXTRAVARS ENVIADOS: {extravars}')
                    
                    # Crear copia temporal del playbook con reemplazo de hosts: target_group
                    pb_path = self.prepare_playbook(sched.playbook.file.path, 'hosts: target_group', f'hosts: {sched.group.name}')
                    
                    # Run Ansible playbook con archivo temporal modificado
                    result = ansible_runner.run(
                        private_data_dir='/opt/www',
                        playbook=pb_path,
                        inventory=inventory_path,
                        extravars=extravars
                    )
                    output = result.stdout.read()
                    sched.output = output
                    sched.status = 'successful' if result.rc == 0 else 'failed'
                    os.remove(inventory_path)
                    os.remove(pb_path)
                else:
                    sched.status = 'failed'
                    sched.output = 'Error: No se pudo determinar el destino.'
            except Exception as e:
                sched.status = 'failed'
                sched.output = str(e)
            sched.executed_at = timezone.now()
            sched.save()
    
    def prepare_playbook(self, playbook_path, find_str, replace_str):
        with open(playbook_path, 'r') as original_pb:
            pb_content = original_pb.read()
        pb_content = pb_content.replace(find_str, replace_str)
        with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.yml') as temp_pb:
            temp_pb.write(pb_content)
            return temp_pb.name
