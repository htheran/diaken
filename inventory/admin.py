from django.contrib import admin
from .models import Environment, Group, Host

# Register your models here.
admin.site.register(Environment)
admin.site.register(Group)
admin.site.register(Host)
