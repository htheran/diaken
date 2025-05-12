from django.contrib import admin
from .models import GlobalSetting, DeploymentCredential

@admin.register(GlobalSetting)
class GlobalSettingAdmin(admin.ModelAdmin):
    list_display = ('key', 'value', 'description')
    search_fields = ('key',)

from .forms import DeploymentCredentialForm

@admin.register(DeploymentCredential)
class DeploymentCredentialAdmin(admin.ModelAdmin):
    form = DeploymentCredentialForm
    list_display = ('name', 'user', 'has_ssh_key')
    def has_ssh_key(self, obj):
        return bool(obj.ssh_private_key_encrypted)
    has_ssh_key.boolean = True
    has_ssh_key.short_description = 'Llave SSH cargada'
    search_fields = ('name', 'user')

# Register your models here.
