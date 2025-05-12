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

    def __str__(self):
        return self.name
