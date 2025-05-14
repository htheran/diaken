#!/usr/bin/env python
import os
import sys
import django

# Configurar el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'diaken.settings')
django.setup()

# Importar la función y modelos necesarios
from deploy.views import get_all_settings_as_dict
from app_settings.models import GlobalSetting

# Obtener y mostrar todas las configuraciones
settings_dict = get_all_settings_as_dict()
print("Configuraciones obtenidas:")
for key, value in settings_dict.items():
    print(f"{key}: {value}")

# Verificar variables críticas
critical_vars = ['server_root', 'log_root', 'http_port', 'https_port', 'domain']
for var in critical_vars:
    if var not in settings_dict:
        print(f"ERROR: Variable crítica '{var}' no encontrada en la configuración")
    else:
        print(f"OK: Variable '{var}' encontrada con valor '{settings_dict[var]}'")

# Crear un diccionario con valores predeterminados para variables faltantes
final_dict = settings_dict.copy()
defaults = {
    'server_root': '/opt/www/sites',
    'log_root': '/var/log/httpd',
    'http_port': '80',
    'https_port': '443',
    'domain': 'example.com'
}

for key, default_value in defaults.items():
    if key not in final_dict or not final_dict[key]:
        final_dict[key] = default_value
        print(f"ADVERTENCIA: Se usó valor predeterminado para '{key}': '{default_value}'")

print("\nDiccionario final de configuración:")
for key, value in final_dict.items():
    print(f"{key}: {value}")
