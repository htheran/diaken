from django import forms
from .models import Environment, Group, Host

class EnvironmentForm(forms.ModelForm):
    class Meta:
        model = Environment
        fields = ['name', 'description']

class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['environment', 'name', 'type', 'description']

from app_settings.models import DeploymentCredential

class HostForm(forms.ModelForm):
    deployment_credential = forms.ModelChoiceField(queryset=DeploymentCredential.objects.all(), required=False, label="Deployment Credential")
    ansible_user = forms.CharField(required=False, label="Usuario (Windows)")
    ansible_password = forms.CharField(required=False, label="Contraseña (Windows)", widget=forms.PasswordInput())
    ansible_port = forms.IntegerField(required=False, initial=5986, widget=forms.HiddenInput())
    ansible_winrm_scheme = forms.CharField(required=False, initial='https', widget=forms.HiddenInput())
    ansible_winrm_server_cert_validation = forms.CharField(required=False, initial='ignore', widget=forms.HiddenInput())
    class Meta:
        model = Host
        fields = [
            'environment', 'group', 'name', 'ip', 'operating_system',
            'ansible_python_interpreter', 'deployment_credential',
            'ansible_user', 'ansible_password',
            'status', 'tags', 'notes']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'
        self.fields['operating_system'].widget = forms.Select(choices=Host.OPERATING_SYSTEM_CHOICES, attrs={'class': 'form-control'})
        if not kwargs.get('instance'):
            self.fields['status'].initial = 1
        # Mostrar siempre todas las credenciales
        self.fields['deployment_credential'].queryset = DeploymentCredential.objects.all()
        # Forzar valor inicial si existe alguna credencial y no hay seleccionada
        if not self.initial.get('deployment_credential') and self.fields['deployment_credential'].queryset.exists():
            self.initial['deployment_credential'] = self.fields['deployment_credential'].queryset.first().pk
        self.fields['ansible_python_interpreter'].widget = forms.TextInput(attrs={'class': 'form-control'})

    def clean(self):
        cleaned_data = super().clean()
        os_value = cleaned_data.get('operating_system')
        cred = cleaned_data.get('deployment_credential')
        ansible_user = cleaned_data.get('ansible_user')
        ansible_password = cleaned_data.get('ansible_password')
        # Set ansible_connection to winrm automatically for Windows hosts
        if os_value == 'Windows':
            cleaned_data['ansible_connection'] = 'winrm'
            cleaned_data['ansible_port'] = 5986
            cleaned_data['ansible_winrm_scheme'] = 'https'
            cleaned_data['ansible_winrm_server_cert_validation'] = 'ignore'
            if not cred or not cred.windows_password_encrypted:
                self.add_error('deployment_credential', 'La credencial seleccionada no tiene contraseña de Windows configurada.')
            if not ansible_user:
                self.add_error('ansible_user', 'El usuario es obligatorio para hosts Windows.')
            if not ansible_password:
                self.add_error('ansible_password', 'La contraseña es obligatoria para hosts Windows.')
        else:
            # Validación SSH para hosts no-Windows
            import socket
            import subprocess
            ip = cleaned_data.get('ip')
            cred = cleaned_data.get('deployment_credential')
            user = cred.user if cred and hasattr(cred, 'user') else None
            keyfile = None
            if cred and hasattr(cred, 'get_ssh_private_key'):
                ssh_key = cred.get_ssh_private_key()
                if ssh_key:
                    import tempfile
                    keyfile = tempfile.NamedTemporaryFile(delete=False, mode='w')
                    keyfile.write(ssh_key.strip() + '\n')
                    keyfile.close()
                    # Validar que la llave privada permita generar la pública
                    import subprocess
                    try:
                        result = subprocess.run(['ssh-keygen', '-y', '-f', keyfile.name], capture_output=True, timeout=5)
                        if result.returncode != 0:
                            self.add_error('deployment_credential', 'La llave privada de la credencial seleccionada es inválida o está corrupta. No se pudo generar la llave pública.')
                    except Exception as e:
                        self.add_error('deployment_credential', f'Error al validar la llave privada: {e}')
            # Intentar conexión SSH
            if ip:
                ssh_args = [
                    'ssh',
                    '-o', 'BatchMode=yes',
                    '-o', 'ConnectTimeout=5',
                    '-o', 'StrictHostKeyChecking=no',
                ]
                if keyfile:
                    ssh_args += ['-i', keyfile.name]
                ssh_args += [f'{user}@{ip}', 'echo ok']
                try:
                    result = subprocess.run(ssh_args, capture_output=True, timeout=8)
                    if result.returncode != 0:
                        import datetime
                        error_msg = result.stderr.decode().strip()
                        self.add_error('ip', f'No se pudo conectar por SSH: {error_msg}')
                        # Guardar log
                        with open('/opt/www/inventory/host_connection_errors.log', 'a') as logf:
                            logf.write(f"[{datetime.datetime.now()}] {user}@{ip} - {error_msg}\n")
                except Exception as e:
                    self.add_error('ip', f'Error de conexión SSH: {e}')
                finally:
                    if keyfile:
                        import os
                        os.unlink(keyfile.name)
        return cleaned_data
