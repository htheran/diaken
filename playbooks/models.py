from django.db import models

# Create your models here.

class Playbook(models.Model):
    OPERATING_SYSTEM_CHOICES = [
        ('Windows', 'Windows'),
        ('RedHat', 'RedHat'),
        ('Debian', 'Debian'),
    ]
    
    name = models.CharField(max_length=255)
    operating_system = models.CharField(max_length=10, choices=OPERATING_SYSTEM_CHOICES)
    file = models.FileField(upload_to='yml/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    tags = models.CharField(max_length=255, blank=True, null=True, help_text="Etiquetas separadas por coma, ej: group,host")
    PLAYBOOK_TYPE_CHOICES = [
        ('host', 'Host'),
        ('group', 'Group'),
    ]
    playbook_type = models.CharField(max_length=10, choices=PLAYBOOK_TYPE_CHOICES, default='group')

    def __str__(self):
        return self.name
