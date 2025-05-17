from django.db import models
import os
from django.core.exceptions import ValidationError

class GlobalSetting(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.key

from cryptography.fernet import Fernet
from django.conf import settings

def validate_file_extension(value):
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.crt', '.key', '.pem']
    if not ext.lower() in valid_extensions:
        raise ValidationError('Unsupported file type. Use .crt, .key or .pem')

class SSLCertificate(models.Model):
    CERTIFICATE_TYPES = [
        ('cert', 'Certificate'),
        ('key', 'Private Key'),
        ('provider', 'Provider Certificate')
    ]
    
    name = models.CharField(max_length=100, help_text="Descriptive name for the certificate")
    certificate_type = models.CharField(max_length=20, choices=CERTIFICATE_TYPES)
    file = models.FileField(upload_to='templates/ssl/', validators=[validate_file_extension])
    uploaded_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        unique_together = ('name', 'certificate_type')
    
    def __str__(self):
        return f"{self.name} - {self.get_certificate_type_display()}"
    
    def save(self, *args, **kwargs):
        # Renombrar el archivo según el tipo de certificado
        if self.certificate_type == 'cert':
            self.file.name = 'certificado.crt'
        elif self.certificate_type == 'key':
            self.file.name = 'certificado.key'
        elif self.certificate_type == 'provider':
            self.file.name = 'certificado-provider.crt'
        super().save(*args, **kwargs)

class DeploymentCredential(models.Model):
    name = models.CharField(max_length=100, unique=True)
    user = models.CharField(max_length=100)
    ssh_private_key_encrypted = models.BinaryField(blank=True, null=True)
    windows_password_encrypted = models.BinaryField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    def set_ssh_private_key(self, key_str):
        f = Fernet(settings.FIELD_ENCRYPTION_KEY)
        self.ssh_private_key_encrypted = f.encrypt(key_str.encode())

    def get_ssh_private_key(self):
        if not self.ssh_private_key_encrypted:
            return None
        f = Fernet(settings.FIELD_ENCRYPTION_KEY)
        return f.decrypt(self.ssh_private_key_encrypted).decode()

    def set_windows_password(self, password_str):
        f = Fernet(settings.FIELD_ENCRYPTION_KEY)
        self.windows_password_encrypted = f.encrypt(password_str.encode())

    def get_windows_password(self):
        if not self.windows_password_encrypted:
            return None
        f = Fernet(settings.FIELD_ENCRYPTION_KEY)
        return f.decrypt(self.windows_password_encrypted).decode()

