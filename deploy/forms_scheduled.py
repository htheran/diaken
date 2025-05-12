from django import forms
from .models import ScheduledDeployment
from playbooks.models import Playbook
from inventory.models import Host, Group
from django.forms import DateTimeInput

class ScheduledDeploymentHostForm(forms.ModelForm):
    class Meta:
        model = ScheduledDeployment
        fields = ['playbook', 'host', 'scheduled_time']
        widgets = {
            'scheduled_time': DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control', 'step': '1'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['playbook'].queryset = Playbook.objects.filter(playbook_type='host').order_by('name')
        self.fields['host'].queryset = Host.objects.all().order_by('name')

class ScheduledDeploymentGroupForm(forms.ModelForm):
    class Meta:
        model = ScheduledDeployment
        fields = ['playbook', 'group', 'scheduled_time']
        widgets = {
            'scheduled_time': DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control', 'step': '1'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['playbook'].queryset = Playbook.objects.filter(playbook_type='group').order_by('name')
        self.fields['group'].queryset = Group.objects.all().order_by('name')
