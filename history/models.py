from django.db import models
from django.conf import settings
from playbooks.models import Playbook
from inventory.models import Host, Group

# Create your models here.

class History(models.Model):
    playbook = models.ForeignKey(Playbook, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, null=True, blank=True, on_delete=models.SET_NULL)
    host = models.ForeignKey(Host, null=True, blank=True, on_delete=models.SET_NULL)
    date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10)
    output = models.TextField()

    def __str__(self):
        return f"{self.playbook.name} - {self.user.username}"
