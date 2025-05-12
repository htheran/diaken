from django.db import models

# Create your models here.

from playbooks.models import Playbook

class PlaybookExecution(models.Model):
    playbook_name = models.CharField(max_length=255)
    operating_system = models.CharField(max_length=10, choices=Playbook.OPERATING_SYSTEM_CHOICES, default='RedHat')
    status = models.CharField(max_length=50)
    executed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.playbook_name} [{self.operating_system}] - {self.status} - {self.executed_at.strftime('%Y-%m-%d %H:%M:%S')}"
