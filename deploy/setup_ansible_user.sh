#!/bin/bash

# CONFIGURA AQUÍ:
USER_TO_CREATE="ansible"        # Cambia por el usuario que desees
PUBKEY_CONTENT=""               # Pega aquí la llave pública (ssh-rsa ...)

# --- NO MODIFICAR DESDE AQUÍ ---
if [ "$(id -u)" -ne 0 ]; then
  echo "Este script debe ejecutarse como root."
  exit 1
fi

if [ -z "$PUBKEY_CONTENT" ]; then
  echo "Debes definir la variable PUBKEY_CONTENT con la llave pública."
  exit 2
fi

if id "$USER_TO_CREATE" &>/dev/null; then
  echo "El usuario $USER_TO_CREATE ya existe."
else
  useradd -m -s /bin/bash "$USER_TO_CREATE"
  echo "Usuario $USER_TO_CREATE creado."
fi

usermod -aG sudo "$USER_TO_CREATE"

mkdir -p /home/"$USER_TO_CREATE"/.ssh
chown "$USER_TO_CREATE":"$USER_TO_CREATE" /home/"$USER_TO_CREATE"/.ssh
chmod 700 /home/"$USER_TO_CREATE"/.ssh

echo "$PUBKEY_CONTENT" > /home/"$USER_TO_CREATE"/.ssh/authorized_keys
chown "$USER_TO_CREATE":"$USER_TO_CREATE" /home/"$USER_TO_CREATE"/.ssh/authorized_keys
chmod 600 /home/"$USER_TO_CREATE"/.ssh/authorized_keys

# Configurar sudo sin password para el usuario
SUDOERS_FILE="/etc/sudoers.d/$USER_TO_CREATE-ansible"
echo "$USER_TO_CREATE ALL=(ALL) NOPASSWD:ALL" > "$SUDOERS_FILE"
chmod 440 "$SUDOERS_FILE"

# Seguridad: no permitir acceso por contraseña
passwd -l "$USER_TO_CREATE"

echo "Usuario $USER_TO_CREATE listo para acceso SSH con llave pública y sudo sin password."
