#!/bin/bash

# Script para crear las plantillas específicas para hosts
# Este script copia las plantillas existentes y las modifica para que funcionen correctamente

# Crear directorio para plantillas de host si no existe
mkdir -p /opt/www/media/templates/host

# Copiar las plantillas originales
cp /opt/www/media/templates/httpd.conf.j2 /opt/www/media/templates/host/httpd.conf.j2
cp /opt/www/media/templates/virtualhost.conf.j2 /opt/www/media/templates/host/virtualhost.conf.j2
cp /opt/www/media/templates/index.html.j2 /opt/www/media/templates/host/index.html.j2

# Reemplazar las referencias a target_group en httpd.conf.j2
sed -i 's/{{ target_group }}-{{ inventory_hostname }}/{{ target_host }}/g' /opt/www/media/templates/host/httpd.conf.j2
sed -i 's/{{ log_root }}/{{ log_root }}\/{{ target_host }}/g' /opt/www/media/templates/host/httpd.conf.j2

# Reemplazar las referencias a target_group en virtualhost.conf.j2
sed -i 's/{{ target_group }}-{{ inventory_hostname }}/{{ target_host }}/g' /opt/www/media/templates/host/virtualhost.conf.j2

# Reemplazar las referencias a target_group en index.html.j2
sed -i 's/{{ target_group }}-{{ inventory_hostname }}/{{ target_host }}/g' /opt/www/media/templates/host/index.html.j2
sed -i 's/<title>{{ inventory_hostname }}/<title>{{ target_host }}/g' /opt/www/media/templates/host/index.html.j2

echo "Plantillas para hosts creadas correctamente en /opt/www/media/templates/host/"
