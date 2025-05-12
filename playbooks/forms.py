from django import forms
from .models import Playbook

class PlaybookForm(forms.ModelForm):
    class Meta:
        model = Playbook
        fields = ['name', 'operating_system', 'file']
