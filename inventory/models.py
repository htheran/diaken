from django.db import models

# Create your models here.

class Environment(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Group(models.Model):
    environment = models.ForeignKey(Environment, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, unique=True)
    type = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Host(models.Model):
    environment = models.ForeignKey(Environment, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, unique=True)
    ip = models.CharField(max_length=15)
    OPERATING_SYSTEM_CHOICES = [
        ('Windows', 'Windows'),
        ('RedHat', 'RedHat'),
        ('Debian', 'Debian'),
    ]
    operating_system = models.CharField(max_length=50, choices=OPERATING_SYSTEM_CHOICES)
    ansible_python_interpreter = models.CharField(max_length=255, default='/usr/bin/python3.9')
    ansible_user = models.CharField(max_length=255, blank=True, null=True)
    ansible_become = models.BooleanField(default=True)
    ansible_become_method = models.CharField(max_length=50, default='sudo')
    # Ansible connection fields
    ansible_connection = models.CharField(max_length=50, blank=True, null=True)
    ansible_port = models.IntegerField(blank=True, null=True)
    # Campos para SSH
    ansible_shell_type = models.CharField(max_length=50, blank=True, null=True, help_text='Tipo de shell a usar (ej: powershell, cmd, bash)')
    ansible_ssh_private_key_file = models.CharField(max_length=255, blank=True, null=True, help_text='Ruta al archivo de llave privada SSH')
    ansible_ssh_common_args = models.TextField(blank=True, null=True, help_text='Argumentos adicionales para SSH')
    # Campos obsoletos
    ansible_winrm_scheme = models.CharField(max_length=10, blank=True, null=True)
    ansible_winrm_server_cert_validation = models.CharField(max_length=20, blank=True, null=True)
    deployment_credential = models.ForeignKey('app_settings.DeploymentCredential', null=True, blank=True, on_delete=models.SET_NULL, help_text='Deployment credential from settings')
    status = models.IntegerField(default=1)
    tags = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
