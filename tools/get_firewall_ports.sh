#!/bin/bash
# Script para obtener los puertos abiertos en firewalld

# Intentar primero con sudo si es posible (sin pedir contraseña)
PORTS=$(sudo -n firewall-cmd --list-ports 2>/dev/null)

# Si no funciona con sudo, intentar sin sudo
if [ -z "$PORTS" ]; then
    PORTS=$(firewall-cmd --list-ports 2>/dev/null)
fi

# Si aún no hay puertos, verificar si firewalld está instalado y activo
if [ -z "$PORTS" ]; then
    # Verificar si firewalld está instalado
    if ! command -v firewall-cmd &> /dev/null; then
        echo "Puertos: firewalld no está instalado"
        exit 0
    fi
    
    # Verificar si firewalld está activo
    ACTIVE=$(systemctl is-active firewalld 2>/dev/null)
    if [ "$ACTIVE" != "active" ]; then
        echo "Puertos: firewalld no está activo"
        exit 0
    fi
    
    echo "No hay puertos abiertos"
else
    echo "Puertos: $PORTS"
fi

# Obtener servicios activos
echo "---SERVICES---"
SERVICES=$(sudo -n firewall-cmd --list-services 2>/dev/null || firewall-cmd --list-services 2>/dev/null)
if [ -z "$SERVICES" ]; then
    echo "No hay servicios activos"
else
    echo "Servicios: $SERVICES"
fi
