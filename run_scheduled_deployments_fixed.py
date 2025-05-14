from django.core.management.base import BaseCommand
from deploy.models import ScheduledDeployment
from django.utils import timezone
from playbooks.models import Playbook
from inventory.models import Host, Group
from django.contrib.auth.models import User
import ansible_runner
import os
import tempfile
from deploy.views import generate_temporary_inventory, get_all_settings_as_dict

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
                # Obtener todas las variables de configuración automáticamente
                extravars = get_all_settings_as_dict()
                
                # Verificar y establecer valores predeterminados para variables críticas
                self._ensure_critical_variables(extravars)
                
                if sched.deploy_type == 'host' and sched.host:
                    # Añadir target_host como variable para las plantillas
                    extravars['target_host'] = sched.host.name
                    self.stdout.write(f'Despliegue a host: {sched.host.name}')
                    self.stdout.write(f'Variables: {extravars}')
                    
                    # --- Lógica similar a deploy_to_host ---
                    inventory_path = generate_temporary_inventory(host_id=sched.host.id)
                    pb_path = self.prepare_playbook(sched.playbook.file.path, 'hosts: target_host', f'hosts: {sched.host.name}')
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
                    # Añadir target_group al diccionario de variables
                    extravars['target_group'] = sched.group.name
                    self.stdout.write(f'Despliegue a grupo: {sched.group.name}')
                    self.stdout.write(f'Variables: {extravars}')
                    
                    # --- Lógica similar a deploy_to_group ---
                    inventory_path = generate_temporary_inventory(group_id=sched.group.id)
                    pb_path = self.prepare_playbook(sched.playbook.file.path, 'hosts: target_group', f'hosts: {sched.group.name}')
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
    
    def _ensure_critical_variables(self, extravars):
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
                self.stdout.write(self.style.WARNING(f'ADVERTENCIA: Variable {key} no definida, usando valor predeterminado: {default_value}'))
                extravars[key] = default_value
            else:
                self.stdout.write(f'Variable {key} = {extravars[key]}')
        
        return extravars

    def prepare_playbook(self, playbook_path, find_str, replace_str):
        with open(playbook_path, 'r') as original_pb:
            pb_content = original_pb.read()
        pb_content = pb_content.replace(find_str, replace_str)
        with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.yml') as temp_pb:
            temp_pb.write(pb_content)
            return temp_pb.name
