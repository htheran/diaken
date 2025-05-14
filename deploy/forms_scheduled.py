from django import forms
from .models import ScheduledDeployment
from playbooks.models import Playbook
from inventory.models import Host, Group
from django.forms import DateTimeInput

class ScheduledDeploymentHostForm(forms.ModelForm):
    # Campos adicionales que no son parte del modelo
    environment = forms.ModelChoiceField(
        queryset=None,
        required=True,
        empty_label="Seleccione un ambiente",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    group = forms.ModelChoiceField(
        queryset=None,
        required=False,  # No es requerido inicialmente porque depende del ambiente seleccionado
        empty_label="Seleccione un grupo",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = ScheduledDeployment
        fields = ['playbook', 'host', 'scheduled_time']
        widgets = {
            'scheduled_time': DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control', 'step': '1'}),
            'playbook': forms.Select(attrs={'class': 'form-control'}),
            'host': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from inventory.models import Environment
        
        # Configurar los querysets iniciales
        self.fields['environment'].queryset = Environment.objects.all().order_by('name')
        self.fields['group'].queryset = Group.objects.all().order_by('name')  # Mostrar todos los grupos inicialmente
        self.fields['host'].queryset = Host.objects.all().order_by('name')  # Mostrar todos los hosts inicialmente
        self.fields['playbook'].queryset = Playbook.objects.filter(playbook_type='host').order_by('name')

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
