from django.db import models
from inventory.models import Host, Group
from playbooks.models import Playbook


class ScheduledDeployment(models.Model):
    DEPLOY_TYPE_CHOICES = [
        ('host', 'Host'),
        ('group', 'Group'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('successful', 'Successful'),
        ('failed', 'Failed'),
    ]
    playbook = models.ForeignKey(Playbook, on_delete=models.CASCADE)
    from django.conf import settings
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    host = models.ForeignKey(Host, null=True, blank=True, on_delete=models.SET_NULL)
    group = models.ForeignKey(Group, null=True, blank=True, on_delete=models.SET_NULL)
    deploy_type = models.CharField(max_length=10, choices=DEPLOY_TYPE_CHOICES)
    scheduled_time = models.DateTimeField()
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='pending')
    output = models.TextField(blank=True, null=True)
    executed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.playbook.name} - {self.get_deploy_type_display()} - {self.scheduled_time}"
