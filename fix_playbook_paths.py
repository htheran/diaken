# Script para corregir rutas erróneas de playbooks en la base de datos
# Uso: python manage.py shell < fix_playbook_paths.py

from playbooks.models import Playbook
import os

# Ruta correcta del directorio de playbooks
DIRECTORIO_CORRECTO = 'yml/'

cambiados = 0
for pb in Playbook.objects.all():
    nombre = os.path.basename(pb.file.name)
    # Solo corregir si la ruta no es la esperada
    if not pb.file.name.startswith(DIRECTORIO_CORRECTO) or '_' in nombre:
        print(f"Corrigiendo playbook {pb.id}: {pb.file.name} -> {DIRECTORIO_CORRECTO + 'Install-Vim.yml'}")
        pb.file.name = DIRECTORIO_CORRECTO + 'Install-Vim.yml'
        pb.save()
        cambiados += 1
print(f"Total de playbooks corregidos: {cambiados}")
