#!/bin/bash
# ============================================================================
# Nombre:         backup_full_system.sh
# Descripción:    Script completo para realizar un backup del sistema Django
#                 incluyendo código, configuraciones, base de datos, paquetes
#                 pip, Ansible y documentación para restauración.
# Uso:            ./backup_full_system.sh [directorio_destino]
# ============================================================================

# Opciones de bash para mejor manejo de errores
set -o pipefail  # Propagar errores en tuberías
trap 'echo "Error en la línea $LINENO. Comando fallido: $BASH_COMMAND"' ERR

# Colores para mensajes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # Sin Color

# Función para mensajes de log
log_message() {
    local level=$1
    local message=$2
    local color=$NC
    
    case $level in
        "INFO") color=$GREEN ;;
        "WARNING") color=$YELLOW ;;
        "ERROR") color=$RED ;;
        "STEP") color=$BLUE ;;
    esac
    
    echo -e "${color}[$level] $message${NC}"
}

# Función para validar comandos
check_command() {
    local cmd=$1
    local pkg=$2
    
    if ! command -v $cmd &> /dev/null; then
        log_message "WARNING" "El comando '$cmd' no está disponible. Algunos datos podrían no respaldarse."
        log_message "INFO" "Puedes instalarlo con: dnf install $pkg"
        return 1
    fi
    return 0
}

# Fecha para el nombre del archivo
DATE=$(date +%Y%m%d_%H%M%S)

# Directorio de destino (por defecto /opt/backup)
BACKUP_DIR=${1:-"/opt/backup"}
TEMP_DIR="$BACKUP_DIR/temp_$DATE"
FINAL_BACKUP="ansible_deployment_backup_$DATE.tar.gz"

# Crear directorios necesarios
log_message "STEP" "Creando directorios para el backup..."
mkdir -p "$TEMP_DIR/inventory" || { log_message "ERROR" "No se pudo crear el directorio $TEMP_DIR/inventory"; exit 1; }
mkdir -p "$TEMP_DIR/app" || { log_message "ERROR" "No se pudo crear el directorio $TEMP_DIR/app"; exit 1; }
mkdir -p "$TEMP_DIR/configs" || { log_message "ERROR" "No se pudo crear el directorio $TEMP_DIR/configs"; exit 1; }
mkdir -p "$TEMP_DIR/database" || { log_message "ERROR" "No se pudo crear el directorio $TEMP_DIR/database"; exit 1; }
mkdir -p "$TEMP_DIR/python" || { log_message "ERROR" "No se pudo crear el directorio $TEMP_DIR/python"; exit 1; }

# ============================================================================
# 1. RECOLECTAR INFORMACIÓN DEL SISTEMA
# ============================================================================
log_message "STEP" "[1/6] Recolectando información del sistema..."

# Información del sistema operativo
log_message "INFO" "Recopilando información del sistema operativo..."
if [ -f /etc/os-release ]; then
    cat /etc/os-release > "$TEMP_DIR/inventory/os-info.txt"
else
    log_message "WARNING" "No se encontró /etc/os-release"
    echo "Sistema operativo desconocido" > "$TEMP_DIR/inventory/os-info.txt"
fi

uname -a >> "$TEMP_DIR/inventory/os-info.txt" 2>/dev/null || log_message "WARNING" "No se pudo ejecutar uname"

# Paquetes instalados
log_message "INFO" "Listando paquetes instalados..."
if check_command dnf "dnf"; then
    dnf list installed > "$TEMP_DIR/inventory/packages-installed.txt" 2>/dev/null || 
    log_message "WARNING" "Error al listar paquetes con dnf"
elif check_command yum "yum"; then
    yum list installed > "$TEMP_DIR/inventory/packages-installed.txt" 2>/dev/null ||
    log_message "WARNING" "Error al listar paquetes con yum"
elif check_command apt "apt"; then
    apt list --installed > "$TEMP_DIR/inventory/packages-installed.txt" 2>/dev/null ||
    log_message "WARNING" "Error al listar paquetes con apt"
else
    log_message "WARNING" "No se pudo determinar el gestor de paquetes"
    echo "No se pudo determinar el gestor de paquetes" > "$TEMP_DIR/inventory/packages-installed.txt"
fi

# Servicios activos
log_message "INFO" "Capturando servicios habilitados..."
if check_command systemctl "systemd"; then
    systemctl list-unit-files --state=enabled > "$TEMP_DIR/inventory/enabled-services.txt" 2>/dev/null ||
    log_message "WARNING" "Error al listar servicios con systemctl"
else
    log_message "WARNING" "systemctl no está disponible"
    echo "No se pudo listar servicios (systemctl no disponible)" > "$TEMP_DIR/inventory/enabled-services.txt"
fi

# Información de kernel y módulos
log_message "INFO" "Registrando información del kernel..."
if check_command lsmod "kmod"; then
    lsmod > "$TEMP_DIR/inventory/kernel-modules.txt" 2>/dev/null ||
    log_message "WARNING" "Error al listar módulos del kernel"
else
    log_message "WARNING" "lsmod no está disponible"
    echo "No se pudo listar módulos del kernel (lsmod no disponible)" > "$TEMP_DIR/inventory/kernel-modules.txt"
fi

# ============================================================================
# 2. INFORMACIÓN DE PYTHON Y PIP
# ============================================================================
log_message "STEP" "[2/6] Capturando información de Python y paquetes..."

# Versiones de Python
if check_command python3 "python3"; then
    python3 --version > "$TEMP_DIR/python/python-info.txt" 2>/dev/null ||
    log_message "WARNING" "Error al obtener la versión de Python"
else
    log_message "WARNING" "python3 no está disponible"
    echo "Python3 no disponible" > "$TEMP_DIR/python/python-info.txt"
fi

# Paquetes pip globales
if check_command pip3 "python3-pip"; then
    log_message "INFO" "Listando paquetes pip globales..."
    echo "=== PAQUETES PIP GLOBALES ===" > "$TEMP_DIR/python/pip-global-packages.txt"
    pip3 freeze >> "$TEMP_DIR/python/pip-global-packages.txt" 2>/dev/null ||
    log_message "WARNING" "Error al listar paquetes con pip freeze"
    
    echo -e "\n=== DETALLE DE PAQUETES INSTALADOS ===" >> "$TEMP_DIR/python/pip-global-packages.txt"
    pip3 list >> "$TEMP_DIR/python/pip-global-packages.txt" 2>/dev/null ||
    log_message "WARNING" "Error al listar paquetes con pip list"
else
    log_message "WARNING" "pip3 no está disponible"
    echo "No se pudo listar paquetes pip (pip3 no disponible)" > "$TEMP_DIR/python/pip-global-packages.txt"
fi

# Información específica de Ansible
log_message "INFO" "Recopilando información de Ansible..."
echo "=== INFORMACIÓN DE ANSIBLE ===" > "$TEMP_DIR/python/ansible-info.txt"
if check_command ansible "ansible"; then
    ansible --version >> "$TEMP_DIR/python/ansible-info.txt" 2>/dev/null ||
    log_message "WARNING" "Error al obtener versión de Ansible"
    
    echo -e "\n=== ANSIBLE COLLECTIONS ===" >> "$TEMP_DIR/python/ansible-info.txt"
    if check_command ansible-galaxy "ansible"; then
        ansible-galaxy collection list >> "$TEMP_DIR/python/ansible-info.txt" 2>/dev/null ||
        log_message "WARNING" "Error al listar colecciones de Ansible"
    else
        echo "ansible-galaxy no disponible" >> "$TEMP_DIR/python/ansible-info.txt"
    fi
    
    # Buscar archivos de configuración de Ansible
    echo -e "\n=== ANSIBLE CONFIG FILES ===" >> "$TEMP_DIR/python/ansible-info.txt"
    if [ -d /etc/ansible ]; then
        find /etc/ansible -type f 2>/dev/null >> "$TEMP_DIR/python/ansible-info.txt" ||
        echo "No se pudieron listar archivos en /etc/ansible" >> "$TEMP_DIR/python/ansible-info.txt"
        
        # Copiar archivos de configuración de Ansible
        log_message "INFO" "Respaldando configuración de Ansible..."
        tar -czf "$TEMP_DIR/configs/ansible-config.tar.gz" /etc/ansible 2>/dev/null ||
        log_message "WARNING" "Error al crear archivo ansible-config.tar.gz"
    else
        echo "No existe el directorio /etc/ansible" >> "$TEMP_DIR/python/ansible-info.txt"
    fi
    
    # Buscar roles de Ansible
    echo -e "\n=== ANSIBLE ROLES ===" >> "$TEMP_DIR/python/ansible-info.txt"
    if [ -d /etc/ansible/roles ]; then
        find /etc/ansible/roles -type d -maxdepth 1 2>/dev/null >> "$TEMP_DIR/python/ansible-info.txt" ||
        echo "No se pudieron listar roles en /etc/ansible/roles" >> "$TEMP_DIR/python/ansible-info.txt"
    else
        echo "No existe el directorio /etc/ansible/roles" >> "$TEMP_DIR/python/ansible-info.txt"
    fi
    
    # Buscar playbooks en el sistema
    echo -e "\n=== ANSIBLE PLAYBOOKS ===" >> "$TEMP_DIR/python/ansible-info.txt"
    find /opt -name "*.yml" -o -name "*.yaml" 2>/dev/null | grep -v "venv" | sort >> "$TEMP_DIR/python/ansible-info.txt" ||
    echo "No se encontraron playbooks en /opt" >> "$TEMP_DIR/python/ansible-info.txt"
else
    log_message "WARNING" "Ansible no está instalado"
    echo "Ansible no está instalado" >> "$TEMP_DIR/python/ansible-info.txt"
fi

# Capturar información de entornos virtuales
log_message "INFO" "Buscando entornos virtuales Python..."
find /opt -name "venv" -type d > "$TEMP_DIR/python/venv-locations.txt" 2>/dev/null || 
echo "No se encontraron entornos virtuales" > "$TEMP_DIR/python/venv-locations.txt"

# Respaldar cada entorno virtual encontrado
if [ -s "$TEMP_DIR/python/venv-locations.txt" ]; then
    log_message "INFO" "Respaldando entornos virtuales encontrados..."
    mkdir -p "$TEMP_DIR/python/venv_packages" || log_message "WARNING" "No se pudo crear directorio para paquetes de venv"
    
    while read -r venv_path; do
        if [ -f "$venv_path/bin/activate" ]; then
            venv_name=$(echo "$venv_path" | sed 's/\//_/g')
            log_message "INFO" "Respaldando entorno virtual: $venv_path"
            source "$venv_path/bin/activate" 2>/dev/null
            if [ $? -eq 0 ]; then
                pip freeze > "$TEMP_DIR/python/venv_packages/requirements_${venv_name}.txt" 2>/dev/null || 
                log_message "WARNING" "Error al ejecutar pip freeze en $venv_path"
                deactivate
            else
                log_message "WARNING" "No se pudo activar el entorno virtual: $venv_path"
            fi
        fi
    done < "$TEMP_DIR/python/venv-locations.txt"
fi

# ============================================================================
# 3. BACKUP DE LA APLICACIÓN
# ============================================================================
log_message "STEP" "[3/6] Realizando backup de la aplicación..."

# Código fuente principal
log_message "INFO" "Copiando código fuente principal..."
if [ -d /opt/www ]; then
    tar -czf "$TEMP_DIR/app/www_source.tar.gz" --exclude="/opt/www/venv" --exclude="/opt/www/artifacts" --exclude="*.pyc" --exclude="__pycache__" /opt/www 2>/dev/null ||
    log_message "WARNING" "Error al crear el archivo www_source.tar.gz"
else
    log_message "WARNING" "El directorio /opt/www no existe"
fi

# Permisos y propietarios
log_message "INFO" "Registrando permisos y propietarios..."
if [ -d /opt/www ]; then
    find /opt/www -type f -exec stat -c "%U:%G %a %n" {} \; > "$TEMP_DIR/app/file-permissions.txt" 2>/dev/null ||
    log_message "WARNING" "Error al listar permisos de archivos"
    
    find /opt/www -type d -exec stat -c "%U:%G %a %n" {} \; > "$TEMP_DIR/app/dir-permissions.txt" 2>/dev/null ||
    log_message "WARNING" "Error al listar permisos de directorios"
else
    log_message "WARNING" "No se pudo listar permisos (directorio /opt/www no existe)"
fi

# ============================================================================
# 4. BACKUP DE LA BASE DE DATOS
# ============================================================================
log_message "STEP" "[4/6] Respaldando base de datos..."

if [ -f /opt/www/manage.py ]; then
    log_message "INFO" "Detectando configuración de Django..."
    cd /opt/www
    if [ -d venv ]; then
        if source venv/bin/activate 2>/dev/null; then
            # Intentar detectar el motor de base de datos
            python manage.py shell -c "from django.conf import settings; print('ENGINE:', settings.DATABASES['default']['ENGINE']); print('NAME:', settings.DATABASES['default']['NAME']); print('USER:', settings.DATABASES.get('default', {}).get('USER', '')); print('HOST:', settings.DATABASES.get('default', {}).get('HOST', ''))" > "$TEMP_DIR/database/db-info.txt" 2>/dev/null || 
            log_message "WARNING" "No se pudo detectar la configuración de Django"
            
            # Extraer información si el archivo existe y no está vacío
            if [ -s "$TEMP_DIR/database/db-info.txt" ]; then
                DB_ENGINE=$(grep "ENGINE:" "$TEMP_DIR/database/db-info.txt" | cut -d' ' -f2- || echo "")
                DB_NAME=$(grep "NAME:" "$TEMP_DIR/database/db-info.txt" | cut -d' ' -f2- || echo "")
                DB_USER=$(grep "USER:" "$TEMP_DIR/database/db-info.txt" | cut -d' ' -f2- || echo "")
                
                log_message "INFO" "Detectado: $DB_ENGINE - $DB_NAME"
                
                # SQLite
                if [[ "$DB_ENGINE" == *"sqlite"* ]]; then
                    log_message "INFO" "Respaldando base de datos SQLite..."
                    if [ -f "$DB_NAME" ]; then
                        cp "$DB_NAME" "$TEMP_DIR/database/database.sqlite3" 2>/dev/null || 
                        log_message "WARNING" "Error al copiar base de datos SQLite"
                        log_message "INFO" "Database backup: SQLite - Éxito"
                    else
                        log_message "WARNING" "Base de datos SQLite no encontrada en $DB_NAME"
                    fi
                
                # PostgreSQL
                elif [[ "$DB_ENGINE" == *"postgresql"* ]]; then
                    log_message "INFO" "Respaldando base de datos PostgreSQL..."
                    if check_command pg_dump "postgresql"; then
                        if [ -z "$DB_USER" ]; then DB_USER="postgres"; fi
                        PGPASSWORD="$PGPASSWORD" pg_dump -U "$DB_USER" -F c -b -v -f "$TEMP_DIR/database/database.dump" "$DB_NAME" 2>/dev/null || 
                        log_message "WARNING" "Error al hacer backup de PostgreSQL"
                        log_message "INFO" "Database backup: PostgreSQL - Verificar si fue exitoso"
                    else
                        log_message "WARNING" "pg_dump no está instalado"
                    fi
                
                # MySQL/MariaDB
                elif [[ "$DB_ENGINE" == *"mysql"* ]]; then
                    log_message "INFO" "Respaldando base de datos MySQL/MariaDB..."
                    if check_command mysqldump "mysql"; then
                        if [ -z "$DB_USER" ]; then DB_USER="root"; fi
                        mysqldump -u "$DB_USER" "$DB_NAME" > "$TEMP_DIR/database/database.sql" 2>/dev/null || 
                        log_message "WARNING" "Error al hacer backup de MySQL"
                        log_message "INFO" "Database backup: MySQL - Verificar si fue exitoso"
                    else
                        log_message "WARNING" "mysqldump no está instalado"
                    fi
                fi
            else
                log_message "WARNING" "No se pudo obtener información de la base de datos"
            fi
            
            deactivate
        else
            log_message "WARNING" "No se pudo activar el entorno virtual"
        fi
    else
        log_message "WARNING" "No se encontró el entorno virtual en /opt/www/venv"
    fi
else
    log_message "WARNING" "No se detectó una aplicación Django en /opt/www"
fi

# ============================================================================
# 5. BACKUP DE CONFIGURACIONES
# ============================================================================
log_message "STEP" "[5/6] Respaldando configuraciones del servidor..."

# Apache/httpd
if [ -d /etc/httpd ]; then
    log_message "INFO" "Respaldando configuración de Apache (httpd)..."
    tar -czf "$TEMP_DIR/configs/httpd-config.tar.gz" /etc/httpd 2>/dev/null ||
    log_message "WARNING" "Error al crear httpd-config.tar.gz"
elif [ -d /etc/apache2 ]; then
    log_message "INFO" "Respaldando configuración de Apache (apache2)..."
    tar -czf "$TEMP_DIR/configs/apache2-config.tar.gz" /etc/apache2 2>/dev/null ||
    log_message "WARNING" "Error al crear apache2-config.tar.gz"
else
    log_message "WARNING" "No se encontró configuración de Apache"
fi

# Nginx
if [ -d /etc/nginx ]; then
    log_message "INFO" "Respaldando configuración de Nginx..."
    tar -czf "$TEMP_DIR/configs/nginx-config.tar.gz" /etc/nginx 2>/dev/null ||
    log_message "WARNING" "Error al crear nginx-config.tar.gz"
fi

# Servicios personalizados
if [ -d /etc/systemd/system ]; then
    log_message "INFO" "Buscando servicios personalizados..."
    mkdir -p "$TEMP_DIR/configs/systemd" || log_message "WARNING" "No se pudo crear directorio systemd"
    
    # Usar find en lugar de un bucle con patrones para copiar los archivos
    find /etc/systemd/system/ -type f \( -name "*django*" -o -name "*gunicorn*" -o -name "*celery*" -o -name "*uwsgi*" -o -name "*daphne*" -o -name "*asgi*" -o -name "*wsgi*" \) -exec cp {} "$TEMP_DIR/configs/systemd/" \; 2>/dev/null
    
    # Verificar si se encontraron archivos
    if [ -z "$(ls -A "$TEMP_DIR/configs/systemd/" 2>/dev/null)" ]; then
        log_message "INFO" "No se encontraron servicios personalizados"
    else
        log_message "INFO" "Servicios personalizados copiados a $TEMP_DIR/configs/systemd/"
    fi
fi

# ============================================================================
# 6. CREAR DOCUMENTACIÓN PARA RESTAURACIÓN
# ============================================================================
log_message "STEP" "[6/6] Generando documentación para restauración..."

cat > "$TEMP_DIR/RESTORE-INSTRUCTIONS.md" << 'EOL'
# Instrucciones para restaurar el sistema

## 1. Requisitos previos
- Oracle Linux 9.5 (o compatible)
- 4 vCPUs y 4GB RAM mínimo
- Python 3.9+

## 2. Pasos para la restauración

### 2.1 Descomprimir el backup
```bash
# Crear un directorio para el backup
mkdir -p /opt/restore
cd /opt/restore

# Descomprimir el archivo principal
tar -xzf ansible_deployment_backup_XXXXXXXX.tar.gz
