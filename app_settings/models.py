from django.db import models

class GlobalSetting(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.key

from cryptography.fernet import Fernet
from django.conf import settings

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
