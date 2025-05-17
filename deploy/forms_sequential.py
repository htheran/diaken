from django import forms
from inventory.models import Environment, Group, Host
from playbooks.models import Playbook

class SequentialPlaybookForm(forms.Form):
    environment = forms.ModelChoiceField(
        queryset=Environment.objects.all().order_by('name'),
        required=True,
        empty_label="Seleccione un ambiente",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    group = forms.ModelChoiceField(
        queryset=Group.objects.all().order_by('name'),
        required=False,
        empty_label="Seleccione un grupo",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    host = forms.ModelChoiceField(
        queryset=Host.objects.all().order_by('name'),
        required=False,
        empty_label="Seleccione un host",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    playbooks = forms.ModelMultipleChoiceField(
        queryset=Playbook.objects.filter(playbook_type='host').order_by('name'),
        required=True,
        widget=forms.SelectMultiple(attrs={'class': 'form-control', 'size': 10})
    )
    playbooks_order = forms.CharField(widget=forms.HiddenInput(), required=False)

    def clean(self):
        cleaned_data = super().clean()
        playbooks = cleaned_data.get('playbooks')
        playbooks_order = cleaned_data.get('playbooks_order')
        if not playbooks or len(playbooks) < 2:
            raise forms.ValidationError('Debe seleccionar al menos 2 playbooks.')
        # Validar que el orden tenga los mismos ids
        if playbooks_order:
            ids = [int(i) for i in playbooks_order.split(',') if i.isdigit()]
            if set(ids) != set(pb.id for pb in playbooks):
                raise forms.ValidationError('El orden de playbooks no coincide con la selección.')
        return cleaned_data
