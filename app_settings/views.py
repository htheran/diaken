from django.shortcuts import render

from django.shortcuts import render, get_object_or_404, redirect
from .models import GlobalSetting, DeploymentCredential
from .forms import GlobalSettingForm, DeploymentCredentialForm

# GLOBAL SETTINGS VIEWS

def global_setting_list(request):
    settings = GlobalSetting.objects.all()
    return render(request, 'app_settings/global_setting_list.html', {'settings': settings})

def global_setting_create(request):
    if request.method == 'POST':
        form = GlobalSettingForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('global_setting_list')
    else:
        form = GlobalSettingForm()
    return render(request, 'app_settings/global_setting_form.html', {'form': form})

def global_setting_update(request, pk):
    setting = get_object_or_404(GlobalSetting, pk=pk)
    if request.method == 'POST':
        form = GlobalSettingForm(request.POST, instance=setting)
        if form.is_valid():
            form.save()
            return redirect('global_setting_list')
    else:
        form = GlobalSettingForm(instance=setting)
    return render(request, 'app_settings/global_setting_form.html', {'form': form, 'setting': setting})

# DEPLOYMENT CREDENTIALS VIEWS

def credential_list(request):
    credentials = DeploymentCredential.objects.all()
    return render(request, 'app_settings/credential_list.html', {'credentials': credentials})

def credential_create(request):
    if request.method == 'POST':
        form = DeploymentCredentialForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('credential_list')
    else:
        form = DeploymentCredentialForm()
    return render(request, 'app_settings/credential_form.html', {'form': form})

def credential_update(request, pk):
    credential = get_object_or_404(DeploymentCredential, pk=pk)
    if request.method == 'POST':
        form = DeploymentCredentialForm(request.POST, instance=credential)
        if form.is_valid():
            form.save()
            return redirect('credential_list')
    else:
        form = DeploymentCredentialForm(instance=credential)
    return render(request, 'app_settings/credential_form.html', {'form': form, 'credential': credential})
