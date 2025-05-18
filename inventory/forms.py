from django import forms
from django.core.exceptions import ValidationError
from .models import Environment, Group, Host
from app_settings.models import DeploymentCredential
import tempfile
import os

class EnvironmentForm(forms.ModelForm):
    class Meta:
        model = Environment
        fields = ['name', 'description']

class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['environment', 'name', 'type', 'description']

class HostForm(forms.ModelForm):
    deployment_credential = forms.ModelChoiceField(
        queryset=DeploymentCredential.objects.all(),
        required=False,
        label="Credencial de Despliegue",
        help_text="Seleccione la credencial que contiene la llave PPK para la conexión SSH"
    )
    ansible_user = forms.CharField(
        required=False,
        label="Usuario",
        help_text="Usuario para la conexión SSH (ej: Administrator)"
    )
    ansible_password = forms.CharField(
        required=False,
        label="Contraseña",
        widget=forms.PasswordInput(render_value=True),
        help_text="Contraseña del usuario (opcional si se usa autenticación por llave)"
    )
    ansible_port = forms.IntegerField(
        required=False,
        initial=22,
        widget=forms.HiddenInput()
    )
    ansible_ssh_private_key_file = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )
    ansible_ssh_common_args = forms.CharField(
        required=False,
        initial='-o StrictHostKeyChecking=no',
        widget=forms.HiddenInput()
    )
    ansible_shell_type = forms.CharField(
        required=False,
        initial='powershell',
        widget=forms.HiddenInput()
    )
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
        
        # Configuración común para todos los sistemas operativos
        cleaned_data['ansible_connection'] = 'ssh'
        cleaned_data['ansible_port'] = 22
        
        # Configuración específica para Windows
        if os_value == 'Windows':
            cleaned_data['ansible_shell_type'] = 'powershell'
            
            # Validaciones para Windows
            if not ansible_user:
                self.add_error('ansible_user', 'El usuario es obligatorio para hosts Windows.')
                
            if not cred:
                self.add_error('deployment_credential', 'Se requiere una credencial para hosts Windows.')
            else:
                # Configurar la llave privada si existe en la credencial
                if hasattr(cred, 'get_ssh_private_key'):
                    ssh_key = cred.get_ssh_private_key()
                    if ssh_key:
                        try:
                            # Crear archivo temporal con la llave privada
                            keyfile = tempfile.NamedTemporaryFile(mode='w', delete=False)
                            keyfile.write(ssh_key)
                            keyfile.close()
                            # Asegurar permisos correctos
                            os.chmod(keyfile.name, 0o600)
                            cleaned_data['ansible_ssh_private_key_file'] = keyfile.name
                            
                            # Omitimos la validación de la llave para permitir cualquier formato
                            # Simplemente verificamos que el archivo exista y tenga contenido
                            if not os.path.exists(keyfile.name) or os.path.getsize(keyfile.name) == 0:
                                self.add_error('deployment_credential', 
                                    'No se pudo crear el archivo de llave privada.')
                            # Registramos que estamos usando la llave
                            print(f"Usando llave SSH: {keyfile.name}")
                            
                            # Nota: Omitimos la validación con ssh-keygen porque puede fallar con llaves en formato PPK
                        except Exception as e:
                            self.add_error('deployment_credential', 
                                f'Error al procesar la llave privada: {str(e)}')
                            if 'keyfile' in locals() and os.path.exists(keyfile.name):
                                os.unlink(keyfile.name)
        
        # Configuración para Linux/Unix
        else:
            cleaned_data['ansible_shell_type'] = 'bash'
            
            # Validación más flexible para Linux
            if not cred:
                # Advertencia en lugar de error para permitir continuar
                print("Advertencia: No se ha seleccionado una credencial para el host Linux.")
            elif hasattr(cred, 'get_ssh_private_key'):
                ssh_key = cred.get_ssh_private_key()
                if ssh_key:
                    try:
                        # Crear archivo temporal con la llave privada
                        keyfile = tempfile.NamedTemporaryFile(mode='w', delete=False)
                        keyfile.write(ssh_key)
                        keyfile.close()
                        # Asegurar permisos correctos
                        os.chmod(keyfile.name, 0o600)
                        cleaned_data['ansible_ssh_private_key_file'] = keyfile.name
                        print(f"Usando llave SSH para Linux: {keyfile.name}")
                    except Exception as e:
                        print(f"Error al procesar la llave SSH para Linux: {e}")
                        # No agregamos error para permitir continuar
        
        # Limpiar campos no utilizados
        cleaned_data['ansible_winrm_scheme'] = None
        cleaned_data['ansible_winrm_server_cert_validation'] = None
        
        return cleaned_data
