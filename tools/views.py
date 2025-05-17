from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from inventory.models import Environment, Group, Host
import json
import subprocess
import re

@login_required
def status_view(request):
    """Vista principal para mostrar el estado de los servicios en un servidor"""
    environments = Environment.objects.all()
    context = {
        'environments': environments,
    }
    return render(request, 'tools/status.html', context)

def run_command_on_host(host, command):
    """Ejecuta un comando en un host remoto y devuelve la salida"""
    import tempfile
    import os
    
    try:
        # Verificar si tenemos la información necesaria para conectar
        if not host.name or not host.ip:
            return {
                'success': False,
                'output': None,
                'error': f"Información de conexión incompleta: nombre={host.name}, IP={host.ip}"
            }
        
        # Obtener las credenciales de despliegue si existen
        ssh_key_file = None
        user = 'root'  # Usuario por defecto
        
        if host.deployment_credential and host.deployment_credential.ssh_private_key_encrypted:
            # Obtener la clave SSH y guardarla en un archivo temporal
            ssh_key = host.deployment_credential.get_ssh_private_key()
            if ssh_key:
                key_bytes = (ssh_key.strip() + '\n').encode('utf-8')
                ssh_key_file = tempfile.NamedTemporaryFile(delete=False, mode='wb', dir='/tmp')
                ssh_key_file.write(key_bytes)
                ssh_key_file.close()
                os.chmod(ssh_key_file.name, 0o600)
                
                # Obtener el usuario de las credenciales de despliegue
                if hasattr(host.deployment_credential, 'user') and host.deployment_credential.user:
                    user = host.deployment_credential.user
        elif host.ansible_user:
            # Si no hay credenciales de despliegue pero hay ansible_user, usarlo
            user = host.ansible_user
            
        # Crear un comando SSH para ejecutar en el host remoto con opciones de seguridad
        ssh_command = f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5"
        
        # Agregar la clave SSH si existe
        if ssh_key_file:
            ssh_command += f" -i {ssh_key_file.name}"
            
        # Completar el comando
        ssh_command += f" {user}@{host.ip} '{command}'"
        print(f"Ejecutando: {ssh_command}")
        
        result = subprocess.run(ssh_command, shell=True, capture_output=True, text=True, timeout=15)
        
        if result.returncode != 0:
            print(f"Error al ejecutar comando: {result.stderr}")
            
        return {
            'success': result.returncode == 0,
            'output': result.stdout.strip(),
            'error': result.stderr.strip() if result.returncode != 0 else None
        }
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'output': None,
            'error': "Tiempo de espera agotado al conectar con el servidor"
        }
    except Exception as e:
        import traceback
        print(f"Error al ejecutar comando: {str(e)}")
        print(traceback.format_exc())
        return {
            'success': False,
            'output': None,
            'error': str(e)
        }

@login_required
def check_service_status(request):
    """API para verificar el estado de los servicios en un host"""
    host_id = request.GET.get('host_id')
    if not host_id:
        return JsonResponse({'error': 'No se proporcionó un host'}, status=400)
    
    try:
        host = Host.objects.get(id=host_id)
    except Host.DoesNotExist:
        return JsonResponse({'error': 'Host no encontrado'}, status=404)
        
    # Verificar que el host tenga la información necesaria para conectarse
    host_config_issues = []
    
    if not host.ip:
        host_config_issues.append('No tiene dirección IP configurada')
    
    # Verificar si tiene credenciales de acceso (ya sea ansible_user o deployment_credential)
    has_credentials = False
    
    # Verificar si tiene credenciales de despliegue con clave SSH
    if host.deployment_credential and host.deployment_credential.ssh_private_key_encrypted:
        has_credentials = True
    # Si no tiene credenciales de despliegue, verificar si tiene ansible_user
    elif not host.ansible_user:
        host_config_issues.append('No tiene usuario configurado para conexión SSH ni credenciales de despliegue')
    else:
        has_credentials = True
    
    # Si hay problemas de configuración, devolver un mensaje detallado
    if host_config_issues:
        # Preparar información de credenciales para mostrar
        credential_info = 'No configurado'
        if host.deployment_credential:
            credential_info = f"Credencial: {host.deployment_credential.name}"
        elif host.ansible_user:
            credential_info = f"Usuario: {host.ansible_user}"
            
        return JsonResponse({
            'error': f'El host {host.name} tiene problemas de configuración: {", ".join(host_config_issues)}',
            'host': {
                'id': host.id,
                'name': host.name,
                'ip': host.ip or 'No configurada',
                'credentials': credential_info,
                'config_issues': host_config_issues
            }
        }, status=200)  # Devolvemos 200 para que el frontend pueda mostrar el error
        
    # Verificar conectividad básica
    test_connection = run_command_on_host(host, 'echo "Conexión exitosa"')
    if not test_connection['success']:
        error_msg = test_connection['error'] or 'No se pudo establecer conexión con el servidor'
        
        # Determinar el tipo de error para dar un mensaje más específico
        error_type = 'conexión'
        error_details = []
        
        # Detectar errores comunes y proporcionar mensajes más útiles
        if 'Connection reset by peer' in error_msg:
            error_type = 'servicio SSH'
            error_details.append('El servicio SSH está rechazando conexiones')
            error_details.append('Es posible que el servicio sshd esté caído o bloqueado por firewall')
        elif 'Connection refused' in error_msg:
            error_type = 'servicio SSH'
            error_details.append('El servicio SSH no está ejecutándose en el servidor')
        elif 'Connection timed out' in error_msg:
            error_type = 'red'
            error_details.append('No se puede acceder al servidor en la red')
            error_details.append('Verifique que el servidor esté encendido y accesible en la red')
        elif 'Host key verification failed' in error_msg:
            error_type = 'autenticación SSH'
            error_details.append('Error de verificación de clave de host')
        
        # Preparar información de credenciales para mostrar
        credential_info = 'No configurado'
        if host.deployment_credential:
            credential_info = f"Credencial: {host.deployment_credential.name}"
        elif host.ansible_user:
            credential_info = f"Usuario: {host.ansible_user}"
            
        return JsonResponse({
            'error': f'Error de {error_type}: {error_msg}',
            'host': {
                'id': host.id,
                'name': host.name,
                'ip': host.ip,
                'credentials': credential_info,
                'error_details': error_details
            }
        }, status=200)  # Devolvemos 200 para que el frontend pueda mostrar el error
    
    # Verificar servicios comunes
    services = {
        'firewalld': {
            'status_cmd': 'systemctl is-active firewalld',
            'info_cmd': 'sudo -n firewall-cmd --list-ports 2>/dev/null || echo "No hay puertos abiertos"; echo "---SERVICES---"; sudo -n firewall-cmd --list-services 2>/dev/null || echo "No hay servicios activos"'
        },
        'httpd': {
            'status_cmd': 'systemctl is-active httpd',
            'info_cmd': 'systemctl status httpd | grep Active'
        },
        'nginx': {
            'status_cmd': 'systemctl is-active nginx',
            'info_cmd': 'systemctl status nginx | grep Active'
        },
        'mariadb': {
            'status_cmd': 'systemctl is-active mariadb',
            'info_cmd': 'systemctl status mariadb | grep Active'
        },
        'postgresql': {
            'status_cmd': 'systemctl is-active postgresql',
            'info_cmd': 'systemctl status postgresql | grep Active'
        },
        'sshd': {
            'status_cmd': 'systemctl is-active sshd',
            'info_cmd': 'systemctl status sshd | grep Active'
        }
    }
    
    # Verificar espacio en disco y memoria
    disk_info = run_command_on_host(host, "df -h | grep -v tmpfs | sort -k5 -r; echo '---DIRECTORY_USAGE---'; sudo -n du -sh /opt /var /home /usr /tmp /root 2>/dev/null || du -sh /opt /var /home /usr /tmp 2>/dev/null || echo 'No se pudo obtener el uso de directorios'")
    
    # Verificar si hay datos de directorios
    if disk_info['success'] and '---DIRECTORY_USAGE---' in disk_info['output']:
        parts = disk_info['output'].split('---DIRECTORY_USAGE---')
        if len(parts) > 1 and not parts[1].strip():
            # Si no hay datos después del separador, intentar con otro comando
            alt_disk_info = run_command_on_host(host, "echo '---DIRECTORY_USAGE---'; find /opt /var /home /usr -maxdepth 0 -exec du -sh {} \; 2>/dev/null")
            if alt_disk_info['success'] and alt_disk_info['output'].strip():
                # Combinar los resultados
                disk_info['output'] = parts[0] + '---DIRECTORY_USAGE---' + alt_disk_info['output']
    
    
    # Verificar la memoria con información detallada
    memory_info = run_command_on_host(host, 'free -h && echo "---MEMORY_DETAILS---" && cat /proc/meminfo | grep -E "MemTotal|MemFree|MemAvailable|Buffers|Cached|SwapTotal|SwapFree|SwapCached"')
    
    
    # Verificar la carga del sistema
    load_info = run_command_on_host(host, "uptime")
    
    # Recopilar el estado de todos los servicios
    service_status = {}
    for service_name, commands in services.items():
        # Verificar si el servicio existe
        status_result = run_command_on_host(host, commands['status_cmd'])
        
        if status_result['success']:
            # El servicio existe y está activo
            info_result = run_command_on_host(host, commands['info_cmd'])
            
            # Para firewalld, procesar la salida para mostrar puertos y servicios
            if service_name == 'firewalld':
                if not info_result['success'] or not info_result['output'] or info_result['output'].strip() == '':
                    info_result['output'] = 'No hay puertos abiertos'
                else:
                    # Dividir la salida en puertos y servicios usando el separador
                    parts = info_result['output'].split('---SERVICES---')
                    
                    # Obtener puertos (primera parte)
                    ports = parts[0].strip() if parts and parts[0].strip() else 'No hay puertos abiertos'
                    
                    # Obtener servicios (segunda parte)
                    services = parts[1].strip() if len(parts) > 1 and parts[1].strip() else 'No hay servicios activos'
                    
                    # Formatear la salida
                    result_parts = []
                    
                    if ports and ports != 'No hay puertos abiertos':
                        result_parts.append(f"Puertos: {ports}")
                    
                    if services and services != 'No hay servicios activos':
                        result_parts.append(f"Servicios: {services}")
                    
                    if result_parts:
                        info_result['output'] = '\n'.join(result_parts)
                    else:
                        info_result['output'] = 'No hay puertos abiertos'
            
            service_status[service_name] = {
                'installed': True,
                'active': True,
                'info': info_result['output']
            }
        else:
            # Verificar si el servicio está instalado pero inactivo
            check_installed = run_command_on_host(host, f"systemctl list-unit-files | grep {service_name}")
            if check_installed['success'] and check_installed['output']:
                service_status[service_name] = {
                    'installed': True,
                    'active': False,
                    'info': 'Servicio instalado pero inactivo'
                }
            else:
                service_status[service_name] = {
                    'installed': False,
                    'active': False,
                    'info': 'Servicio no instalado'
                }
    
    # Procesar información de disco
    disk_data = []
    directory_usage = []
    
    if disk_info['success']:
        # Dividir la salida en información de particiones y uso de directorios
        parts = disk_info['output'].split('---DIRECTORY_USAGE---')
        df_output = parts[0].strip()
        dir_output = parts[1].strip() if len(parts) > 1 else ''
        
        # Procesar información de particiones (df -h)
        for line in df_output.split('\n'):
            if line.strip():
                parts = line.split()
                if len(parts) >= 6:
                    usage_percent = parts[4].replace('%', '')
                    try:
                        usage_percent = int(usage_percent)
                        # Solo marcar como alerta si supera el 70%
                        alert = usage_percent > 70
                    except ValueError:
                        alert = False
                    
                    disk_data.append({
                        'filesystem': parts[0],
                        'size': parts[1],
                        'used': parts[2],
                        'available': parts[3],
                        'percent': parts[4],
                        'percent_num': usage_percent if isinstance(usage_percent, int) else 0,
                        'mounted': parts[5],
                        'alert': alert
                    })
        
        # Procesar información de uso de directorios (du -sh)
        if dir_output:
            # Eliminar mensajes de error comunes que podrían aparecer en la salida
            error_patterns = ['No se pudo obtener', 'Permission denied', 'cannot access', 'du: cannot']
            has_error = any(error in dir_output for error in error_patterns)
            
            # Solo procesar si no hay errores evidentes
            if not has_error:
                for line in dir_output.split('\n'):
                    if line.strip():
                        # Manejar diferentes formatos de salida (con o sin tabulaciones)
                        parts = line.split()
                        if len(parts) >= 2:
                            size = parts[0]
                            # Unir el resto como directorio en caso de espacios en nombres
                            directory = ' '.join(parts[1:])
                            
                            # Ignorar líneas que no parecen contener información de tamaño válida
                            if not re.search(r'[0-9]', size):
                                continue
                                
                            # Limpiar la ruta del directorio
                            directory = directory.rstrip('/')
                            
                            # Calcular porcentaje aproximado basado en el tamaño del sistema de archivos raíz
                            # Primero buscar la partición específica donde está montado el directorio
                            target_fs = None
                            for fs in disk_data:
                                if directory.startswith(fs['mounted']) and (not target_fs or len(fs['mounted']) > len(target_fs['mounted'])):
                                    target_fs = fs
                            
                            # Si no encontramos una partición específica, usar la raíz
                            if not target_fs:
                                target_fs = next((fs for fs in disk_data if fs['mounted'] == '/'), None)
                                
                            if target_fs:
                                try:
                                    # Función mejorada para convertir tamaños a bytes
                                    def convert_to_bytes(value):
                                        value = value.lower()
                                        num = float(re.sub(r'[^\d.]', '', value))
                                        if 'g' in value or 'gi' in value:
                                            return num * 1024 * 1024 * 1024  # Convertir GB/GiB a bytes
                                        elif 'm' in value or 'mi' in value:
                                            return num * 1024 * 1024  # Convertir MB/MiB a bytes
                                        elif 'k' in value or 'ki' in value:
                                            return num * 1024  # Convertir KB/KiB a bytes
                                        elif 't' in value or 'ti' in value:
                                            return num * 1024 * 1024 * 1024 * 1024  # Convertir TB/TiB a bytes
                                        else:
                                            return num  # Asumir que ya está en bytes
                                    
                                    dir_size_bytes = convert_to_bytes(size)
                                    fs_size_bytes = convert_to_bytes(target_fs['size'])
                                    
                                    # Calcular porcentaje con límite de 100%
                                    if fs_size_bytes > 0:
                                        percent = min((dir_size_bytes / fs_size_bytes) * 100, 100.0)
                                    else:
                                        percent = 0
                                        
                                    percent_str = f"{percent:.1f}%"
                                    alert = percent > 70
                                except (ValueError, ZeroDivisionError):
                                    percent = 0
                                    percent_str = "0%"
                                    alert = False
                            else:
                                percent = 0
                                percent_str = "N/A"
                                alert = False
                            
                            # Solo agregar directorios con tamaño significativo (más de 1MB)
                            if 'k' not in size.lower() or float(re.sub(r'[^\d.]', '', size)) > 900:
                                directory_usage.append({
                                    'directory': directory,
                                    'size': size,
                                    'percent': percent_str,
                                    'percent_num': percent,
                                    'alert': alert
                                })
    
    # Añadir uso de directorios a la información de disco
    disk_data = {
        'filesystems': disk_data,
        'directories': directory_usage
    }
    
    # Procesar información de memoria
    memory_data = {}
    if memory_info['success']:
        output = memory_info['output']
        
        # Dividir la salida en la parte de free -h y la parte de /proc/meminfo
        parts = output.split('---MEMORY_DETAILS---')
        free_output = parts[0].strip()
        meminfo_output = parts[1].strip() if len(parts) > 1 else ''
        
        # Procesar la salida de free -h
        free_lines = free_output.split('\n')
        if len(free_lines) >= 2:
            mem_parts = free_lines[1].split()
            if len(mem_parts) >= 7:
                total = mem_parts[1]
                used = mem_parts[2]
                free = mem_parts[3]
                shared = mem_parts[4] if len(mem_parts) > 4 else 'N/A'
                buff_cache = mem_parts[5] if len(mem_parts) > 5 else 'N/A'
                available = mem_parts[6] if len(mem_parts) > 6 else 'N/A'
                
                # Calcular el porcentaje de uso
                try:
                    # Convertir valores a una unidad común (MB) para comparar correctamente
                    def convert_to_mb(value):
                        value = value.lower()
                        num = float(re.sub(r'[^\d.]', '', value))
                        if 'gi' in value:
                            return num * 1024  # Convertir GB a MB
                        elif 'mi' in value:
                            return num  # Ya está en MB
                        elif 'ki' in value:
                            return num / 1024  # Convertir KB a MB
                        else:
                            return num  # Asumir que ya está en MB
                    
                    total_mb = convert_to_mb(total)
                    used_mb = convert_to_mb(used)
                    
                    # Calcular porcentaje
                    percent = (used_mb / total_mb) * 100 if total_mb > 0 else 0
                    
                    # Solo marcar como alerta si supera el 90%
                    alert = percent > 90
                except (ValueError, ZeroDivisionError):
                    percent = 0
                    alert = False
                
                memory_data = {
                    'total': total,
                    'used': used,
                    'free': free,
                    'shared': shared,
                    'buff_cache': buff_cache,
                    'available': available,
                    'percent': f"{percent:.1f}%",
                    'percent_num': percent,
                    'alert': alert,
                    'details': {}
                }
                
                # Procesar información detallada de /proc/meminfo
                if meminfo_output:
                    meminfo_lines = meminfo_output.split('\n')
                    for line in meminfo_lines:
                        if ':' in line:
                            key, value = line.split(':', 1)
                            key = key.strip()
                            value = value.strip()
                            # Convertir a formato legible
                            if 'kB' in value:
                                value_num = int(value.replace('kB', '').strip())
                                # Convertir a MB o GB según el tamaño
                                if value_num > 1048576:  # > 1GB
                                    value = f"{value_num/1048576:.2f} GB"
                                else:
                                    value = f"{value_num/1024:.0f} MB"
                            memory_data['details'][key] = value
                
            # Añadir información de swap si está disponible
            if len(free_lines) >= 3 and 'Swap' in free_lines[2]:
                swap_parts = free_lines[2].split()
                if len(swap_parts) >= 4:
                    swap_total = swap_parts[1]
                    swap_used = swap_parts[2]
                    swap_free = swap_parts[3]
                    
                    try:
                        # Convertir a valores numéricos considerando las unidades (Mi, Gi, etc.)
                        def convert_to_bytes(value):
                            value = value.lower()
                            num = float(re.sub(r'[^\d.]', '', value))
                            if 'gi' in value:
                                return num * 1024 * 1024 * 1024  # Convertir GiB a bytes
                            elif 'mi' in value:
                                return num * 1024 * 1024  # Convertir MiB a bytes
                            elif 'ki' in value:
                                return num * 1024  # Convertir KiB a bytes
                            elif 'g' in value:
                                return num * 1000 * 1000 * 1000  # Convertir GB a bytes
                            elif 'm' in value:
                                return num * 1000 * 1000  # Convertir MB a bytes
                            elif 'k' in value:
                                return num * 1000  # Convertir KB a bytes
                            else:
                                return num  # Asumir que ya está en bytes
                        
                        swap_total_bytes = convert_to_bytes(swap_total)
                        swap_used_bytes = convert_to_bytes(swap_used)
                        
                        # Asegurarse de que el porcentaje no exceda el 100%
                        if swap_total_bytes > 0:
                            swap_percent = min((swap_used_bytes / swap_total_bytes) * 100, 100.0)
                        else:
                            swap_percent = 0
                            
                        swap_alert = swap_percent > 70
                    except (ValueError, ZeroDivisionError):
                        swap_percent = 0
                        swap_alert = False
                    
                    # Obtener información adicional de swap de meminfo
                    swap_cached = 'N/A'
                    if meminfo_output and 'SwapCached' in meminfo_output:
                        for line in meminfo_output.split('\n'):
                            if 'SwapCached:' in line:
                                swap_cached_value = line.split(':', 1)[1].strip()
                                if 'kB' in swap_cached_value:
                                    swap_cached_num = int(swap_cached_value.replace('kB', '').strip())
                                    if swap_cached_num > 1024:
                                        swap_cached = f"{swap_cached_num/1024:.0f} MB"
                                    else:
                                        swap_cached = f"{swap_cached_num} KB"
                    
                    memory_data['swap'] = {
                        'total': swap_total,
                        'used': swap_used,
                        'free': swap_free,
                        'cached': swap_cached,
                        'percent': f"{swap_percent:.1f}%",
                        'percent_num': swap_percent,
                        'alert': swap_alert
                    }
    
    # Procesar información de carga del sistema
    load_data = {}
    if load_info['success']:
        # Extraer los valores de carga (load average)
        load_match = re.search(r'load average: ([\d.]+), ([\d.]+), ([\d.]+)', load_info['output'])
        if load_match:
            load_1m = float(load_match.group(1))
            load_5m = float(load_match.group(2))
            load_15m = float(load_match.group(3))
            
            # Extraer el tiempo de actividad
            uptime_match = re.search(r'up\s+(.*?),\s+\d+\s+user', load_info['output'])
            uptime = uptime_match.group(1) if uptime_match else "desconocido"
            
            # Obtener el número de CPUs para contextualizar la carga
            cpu_info = run_command_on_host(host, "nproc")
            num_cpus = 1  # Valor por defecto
            if cpu_info['success'] and cpu_info['output'].strip().isdigit():
                num_cpus = int(cpu_info['output'].strip())
            
            # La carga del sistema representa el número promedio de procesos
            # que están en ejecución o esperando recursos. Un valor mayor que
            # el número de CPUs indica sobrecarga.
            load_threshold = num_cpus * 0.7  # 70% de capacidad como umbral
            
            load_data = {
                'uptime': uptime,
                'load_1m': load_1m,
                'load_5m': load_5m,
                'load_15m': load_15m,
                'num_cpus': num_cpus,
                'explanation': 'La carga del sistema indica el número promedio de procesos activos. ' +
                              f'Con {num_cpus} CPU(s), valores superiores a {num_cpus} indican sobrecarga.',
                'alert': load_1m > load_threshold  # Alerta si la carga supera el 70% de las CPUs disponibles
            }
    
    # Devolver toda la información recopilada
    return JsonResponse({
        'host': {
            'name': host.name,
            'ip': host.ip
        },
        'services': service_status,
        'disk': disk_data,
        'memory': memory_data,
        'load': load_data
    })

@login_required
def api_groups(request):
    """API para obtener grupos por ambiente"""
    environment_id = request.GET.get('environment_id')
    groups = Group.objects.filter(environment_id=environment_id).values('id', 'name')
    return JsonResponse({'groups': list(groups)})

@login_required
def api_hosts(request):
    """API para obtener hosts por grupo"""
    group_id = request.GET.get('group_id')
    hosts = Host.objects.filter(group_id=group_id).values('id', 'name')
    return JsonResponse({'hosts': list(hosts)})
