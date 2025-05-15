from django import forms
from .models import GlobalSetting, DeploymentCredential, SSLCertificate

class GlobalSettingForm(forms.ModelForm):
    class Meta:
        model = GlobalSetting
        fields = ['key', 'value', 'description']

class DeploymentCredentialForm(forms.ModelForm):
    windows_password = forms.CharField(
        label="Windows Password",
        widget=forms.PasswordInput(render_value=False),
        required=False,
        help_text="Only for Windows hosts. Stored encrypted."
    )
    ssh_private_key = forms.CharField(
        label="SSH Private Key",
        widget=forms.Textarea(attrs={"rows": 6}),
        required=False,
        help_text="Paste the private key in PEM format here. It will be stored encrypted."
    )

    class Meta:
        model = DeploymentCredential
        fields = ['name', 'user', 'ssh_private_key', 'windows_password', 'notes']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If there's already a password, don't show the value
        if self.instance and self.instance.pk and self.instance.windows_password_encrypted:
            self.fields['windows_password'].help_text += " (A password already exists. Leave blank to keep it unchanged.)"

class SSLCertificateForm(forms.ModelForm):
    class Meta:
        model = SSLCertificate
        fields = ['name', 'certificate_type', 'file', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'certificate_type': forms.Select(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        help_texts = {
            'name': 'Descriptive name to identify this certificate',
            'certificate_type': 'Type of certificate you are uploading',
            'file': 'Certificate file (.crt, .key, .pem)',
            'notes': 'Additional notes about this certificate (optional)',
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If we're editing an existing certificate
        if self.instance and self.instance.pk:
            self.fields['file'].required = False
            self.fields['file'].help_text = "Leave blank to keep the current file. Upload a new file to replace it."

    def clean_ssh_private_key(self):
        key = self.cleaned_data.get('ssh_private_key')
        if not key and not self.instance.pk:
            raise forms.ValidationError("You must enter a SSH private key.")
        if key:
            if not key.strip().startswith('-----BEGIN'):
                raise forms.ValidationError("The key must start with '-----BEGIN ...'.")
            if not '-----END' in key:
                raise forms.ValidationError("The key must contain '-----END ...'.")
            if len(key.strip()) < 1000:
                raise forms.ValidationError("The key seems too short to be valid.")
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
