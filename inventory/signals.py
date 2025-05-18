from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Host
import subprocess
import os

@receiver(post_save, sender=Host)
def provision_deploy_user(sender, instance, created, **kwargs):
    if created and instance.deployment_credential:
        deploy_user = instance.deployment_credential.user
        # Obtener la llave privada SSH desde la base de datos
        ssh_private_key = instance.deployment_credential.get_ssh_private_key()
        if not ssh_private_key:
            print("No hay llave privada SSH configurada.")
            return

        # Guardar la llave privada temporalmente
        key_path = f"/tmp/ssh_key_{instance.pk}"
        with open(key_path, "w") as keyfile:
            keyfile.write(ssh_private_key)
        os.chmod(key_path, 0o600)

        # Intentar generar la llave pública usando ssh-keygen (opcional)
        ssh_pubkey = ""
        try:
            # Intentar generar la llave pública, pero no es crítico si falla
            result = subprocess.run(["ssh-keygen", "-y", "-f", key_path], 
                                   capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                ssh_pubkey = result.stdout.strip()
            else:
                print(f"Aviso: No se pudo generar la llave pública. Esto es normal para llaves en formato PPK.")
                print(f"Detalles: {result.stderr}")
        except Exception as e:
            print(f"Aviso: Error al intentar generar la llave pública: {e}")
            # Continuamos sin la llave pública, no es crítico

        # Crear un inventario más robusto con opciones para evitar problemas de autenticación
        inventory_content = f"[target]\n{instance.ip} ansible_user=root ansible_ssh_private_key_file={key_path} ansible_ssh_common_args='-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'\n"
        inventory_path = f"/tmp/inventory_host_{instance.pk}"
        with open(inventory_path, "w") as invfile:
            invfile.write(inventory_content)

        # Configurar variables de entorno para Ansible
        env = os.environ.copy()
        env['ANSIBLE_HOST_KEY_CHECKING'] = 'False'

        # Construir el comando con opciones para mayor tolerancia a fallos
        cmd = [
            "ansible-playbook",
            "/opt/www/playbooks/provision_user.yml",
            "-i", inventory_path,
            "--extra-vars", f"deploy_user={deploy_user} ssh_pubkey='{ssh_pubkey}'",
            "--timeout", "30",
            "--forks", "1"
        ]

        # Ejecutar el playbook, pero no fallar si hay errores
        try:
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"Provisionamiento exitoso para {instance.ip}")
            else:
                print(f"Aviso: El provisionamiento no se completó correctamente, pero el host se ha guardado.")
                print(f"Detalles: {result.stderr}")
        except Exception as e:
            print(f"Aviso: Error al ejecutar el provisionamiento: {e}")
            print("El host se ha guardado correctamente a pesar del error.")
        finally:
            # Limpiar archivos temporales
            try:
                os.remove(inventory_path)
                os.remove(key_path)
            except Exception:
                pass
