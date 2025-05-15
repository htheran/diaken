from django.shortcuts import render

from django.shortcuts import render, get_object_or_404, redirect
from .models import GlobalSetting, DeploymentCredential, SSLCertificate
from .forms import GlobalSettingForm, DeploymentCredentialForm, SSLCertificateForm

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

# SSL CERTIFICATE VIEWS

def ssl_certificate_list(request):
    certificates = SSLCertificate.objects.all().order_by('certificate_type', 'name')
    # Agrupar certificados por tipo
    cert_groups = {
        'cert': certificates.filter(certificate_type='cert'),
        'key': certificates.filter(certificate_type='key'),
        'provider': certificates.filter(certificate_type='provider')
    }
    return render(request, 'app_settings/ssl_certificate_list.html', {'cert_groups': cert_groups})

def ssl_certificate_create(request):
    if request.method == 'POST':
        form = SSLCertificateForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('ssl_certificate_list')
    else:
        form = SSLCertificateForm()
    return render(request, 'app_settings/ssl_certificate_form.html', {'form': form})

def ssl_certificate_update(request, pk):
    certificate = get_object_or_404(SSLCertificate, pk=pk)
    if request.method == 'POST':
        form = SSLCertificateForm(request.POST, request.FILES, instance=certificate)
        if form.is_valid():
            # Si no se proporciona un nuevo archivo, mantener el existente
            if not form.cleaned_data.get('file'):
                form.instance.file = certificate.file
            form.save()
            return redirect('ssl_certificate_list')
    else:
        form = SSLCertificateForm(instance=certificate)
    return render(request, 'app_settings/ssl_certificate_form.html', {'form': form, 'certificate': certificate})

def ssl_certificate_delete(request, pk):
    certificate = get_object_or_404(SSLCertificate, pk=pk)
    if request.method == 'POST':
        certificate.delete()
        return redirect('ssl_certificate_list')
    return render(request, 'app_settings/ssl_certificate_confirm_delete.html', {'certificate': certificate})
