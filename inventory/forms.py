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
        if os_value == 'Windows':
            if not cred or not cred.windows_password_encrypted:
                self.add_error('deployment_credential', 'La credencial seleccionada no tiene contraseña de Windows configurada.')
            if not ansible_user:
                self.add_error('ansible_user', 'El usuario es obligatorio para hosts Windows.')
            if not ansible_password:
                self.add_error('ansible_password', 'La contraseña es obligatoria para hosts Windows.')
        else:
            # Ya filtramos el queryset, así que no es necesario validar aquí
            pass
        return cleaned_data
