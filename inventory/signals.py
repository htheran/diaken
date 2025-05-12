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

        # Generar la llave pública usando ssh-keygen
        ssh_pubkey = ""
        try:
            ssh_pubkey = subprocess.check_output(["ssh-keygen", "-y", "-f", key_path]).decode().strip()
        except Exception as e:
            print(f"Error generando la llave pública: {e}")
            # Si no es crítico, puedes continuar sin la pública

        inventory_content = f"{instance.ip} ansible_user=root ansible_ssh_private_key_file={key_path}\n"
        inventory_path = f"/tmp/inventory_host_{instance.pk}"
        with open(inventory_path, "w") as invfile:
            invfile.write(inventory_content)

        cmd = [
            "ansible-playbook",
            "/opt/www/playbooks/provision_user.yml",
            "-i", inventory_path,
            "--extra-vars", f"deploy_user={deploy_user} ssh_pubkey='{ssh_pubkey}'"
        ]
        try:
            subprocess.run(cmd, check=True)
            print(f"Provisionamiento exitoso para {instance.ip}")
        except Exception as e:
            print(f"Error ejecutando Ansible: {e}")
        finally:
            try:
                os.remove(inventory_path)
                os.remove(key_path)
            except Exception:
                pass
