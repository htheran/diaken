from django import forms
from .models import GlobalSetting, DeploymentCredential

class GlobalSettingForm(forms.ModelForm):
    class Meta:
        model = GlobalSetting
        fields = ['key', 'value', 'description']

class DeploymentCredentialForm(forms.ModelForm):
    windows_password = forms.CharField(
        label="Windows Password",
        widget=forms.PasswordInput(render_value=False),
        required=False,
        help_text="Solo para hosts Windows. Se almacena cifrada."
    )
    ssh_private_key = forms.CharField(
        label="Llave privada SSH",
        widget=forms.Textarea(attrs={"rows": 6}),
        required=False,
        help_text="Pega aquí la llave privada en formato PEM. Se almacena cifrada."
    )

    class Meta:
        model = DeploymentCredential
        fields = ['name', 'user', 'ssh_private_key', 'windows_password', 'notes']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si ya hay contraseña, no mostrar el valor
        if self.instance and self.instance.pk and self.instance.windows_password_encrypted:
            self.fields['windows_password'].help_text += " (Ya existe una contraseña. Deja vacío para no cambiarla.)"
        if self.instance and self.instance.pk and self.instance.ssh_private_key_encrypted:
            self.fields['ssh_private_key'].help_text += " (Ya existe una llave privada. Deja vacío para no cambiarla.)"

    def clean_ssh_private_key(self):
        key = self.cleaned_data.get('ssh_private_key')
        if not key and not self.instance.pk:
            raise forms.ValidationError("Debes ingresar una llave privada SSH.")
        if key:
            if not key.strip().startswith('-----BEGIN'):
                raise forms.ValidationError("La llave debe comenzar con '-----BEGIN ...'.")
            if not key.strip().endswith('PRIVATE KEY-----'):
                raise forms.ValidationError("La llave debe terminar con 'PRIVATE KEY-----'.")
            if len(key.strip()) < 1000:
                raise forms.ValidationError("La llave parece demasiado corta para ser válida.")
        return key

    def save(self, commit=True):
        instance = super().save(commit=False)
        pwd = self.cleaned_data.get('windows_password')
        if pwd:
            instance.set_windows_password(pwd)
        elif not self.instance.pk:
            instance.windows_password_encrypted = None
        key = self.cleaned_data.get('ssh_private_key')
        if key:
            instance.set_ssh_private_key(key)
        elif self.instance.pk and not key:
            # Si está editando y deja el campo vacío, NO sobreescribir la llave existente
            pass
        elif not self.instance.pk:
            instance.ssh_private_key_encrypted = None
        if commit:
            instance.save()
        return instance
