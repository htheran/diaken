from django.shortcuts import render
from inventory.models import Environment, Group, Host
from django.db.models import Count

# Create your views here.

from playbooks.models import Playbook
from django.db.models.functions import TruncDate
from django.db.models import Count
import json

# Funciones auxiliares para manipular colores
def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb):
    return '#{:02x}{:02x}{:02x}'.format(int(rgb[0]), int(rgb[1]), int(rgb[2]))

def darken_color(hex_color, factor=0.1):
    r, g, b = hex_to_rgb(hex_color)
    r = max(0, r * (1 - factor))
    g = max(0, g * (1 - factor))
    b = max(0, b * (1 - factor))
    return rgb_to_hex((r, g, b))

def lighten_color(hex_color, factor=0.1):
    r, g, b = hex_to_rgb(hex_color)
    r = min(255, r + (255 - r) * factor)
    g = min(255, g + (255 - g) * factor)
    b = min(255, b + (255 - b) * factor)
    return rgb_to_hex((r, g, b))

def desaturate_color(hex_color, factor=0.1):
    r, g, b = hex_to_rgb(hex_color)
    gray = 0.2989 * r + 0.5870 * g + 0.1140 * b
    r = r * (1 - factor) + gray * factor
    g = g * (1 - factor) + gray * factor
    b = b * (1 - factor) + gray * factor
    return rgb_to_hex((r, g, b))

def playbook_executions_view(request):
    import logging
    from collections import defaultdict
    import json as pyjson
    from django.db import connection
    from datetime import datetime, timedelta
    from django.db.models import Count
    from history.models import History
    from inventory.models import Host
    from playbooks.models import Playbook

    # Obtener datos para el gráfico principal
    # Últimos 7 días por defecto
    days = int(request.GET.get('days', 7))
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    raw_sql = '''
        SELECT p.name as playbook_name, p.operating_system, h.status, 
               DATE(h.date) as date, COUNT(*) as count,
               COALESCE(h.host_id, 0) as host_id,
               COALESCE(h.group_id, 0) as group_id
        FROM history_history h
        JOIN playbooks_playbook p ON h.playbook_id = p.id
        WHERE DATE(h.date) >= %s AND DATE(h.date) <= %s
        GROUP BY p.name, p.operating_system, h.status, DATE(h.date), host_id, group_id
        ORDER BY date DESC;
    '''
    
    with connection.cursor() as cursor:
        cursor.execute(raw_sql, [start_date, end_date])
        rows = cursor.fetchall()

    records = []
    for row in rows:
        records.append({
            'playbook_name': row[0],
            'operating_system': row[1],
            'status': row[2],
            'date': row[3],
            'count': row[4],
            'host_id': row[5],
            'group_id': row[6]
        })

    # Obtener nombres de hosts para los IDs
    host_ids = {r['host_id'] for r in records if r['host_id'] > 0}
    hosts_map = {}
    if host_ids:
        hosts = Host.objects.filter(id__in=host_ids)
        hosts_map = {h.id: h.name for h in hosts}

    # Preparar datos para el gráfico principal
    all_dates = sorted({r['date'] for r in records})
    if not all_dates:  # Si no hay datos, mostrar los últimos 7 días vacíos
        all_dates = [(end_date - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(days-1, -1, -1)]
    
    labels = all_dates
    
    # Agrupar por playbook y status para el gráfico principal
    unique_keys = sorted({(r['playbook_name'], r['status']) for r in records})
    grouped = {key: [0]*len(labels) for key in unique_keys}
    
    # Crear una paleta de colores amplia y distintiva
    color_palette = [
        # Colores principales
        '#FF5733', '#33FF57', '#3357FF', '#FF33F5', '#F5FF33', '#33FFF5', 
        '#8033FF', '#FF8033', '#33FF80', '#8080FF', '#FF8080', '#80FF80',
        # Colores secundarios
        '#FF2D00', '#00FF2D', '#2D00FF', '#FF002D', '#2DFF00', '#002DFF',
        '#AA00FF', '#FFAA00', '#00FFAA', '#00AAFF', '#FF00AA', '#AAFF00',
        # Colores terciarios
        '#CC5200', '#52CC00', '#0052CC', '#CC0052', '#00CC52', '#5200CC',
        '#7A00CC', '#CC7A00', '#00CC7A', '#007ACC', '#CC007A', '#7ACC00',
        # Tonos de azul
        '#0000FF', '#0066FF', '#00CCFF', '#3300FF', '#3366FF', '#33CCFF',
        # Tonos de verde
        '#00FF00', '#00FF66', '#00FFCC', '#33FF00', '#33FF66', '#33FFCC',
        # Tonos de rojo
        '#FF0000', '#FF0066', '#FF00CC', '#FF3300', '#FF3366', '#FF33CC',
        # Tonos de amarillo
        '#FFFF00', '#FFFF66', '#FFFFCC', '#FFCC00', '#FFCC66', '#FFCCCC',
        # Tonos de púrpura
        '#9900FF', '#9933FF', '#9966FF', '#CC00FF', '#CC33FF', '#CC66FF',
        # Tonos de naranja
        '#FF9900', '#FF9933', '#FF9966', '#FFCC00', '#FFCC33', '#FFCC66'
    ]
    
    # Crear un diccionario para asignar un color único a cada combinación de playbook+status
    playbook_status_colors = {}
    color_index = 0
    
    # Primero, identificar todos los playbooks únicos
    unique_playbooks = sorted({key[0] for key in unique_keys})
    
    # Asignar un color base a cada playbook
    playbook_base_colors = {}
    for playbook in unique_playbooks:
        playbook_base_colors[playbook] = color_palette[color_index % len(color_palette)]
        color_index += 1
    
    key_labels = []
    key_colors = []
    
    for key in unique_keys:
        playbook, status = key
        # Formatear el nombre del playbook para que sea más legible
        playbook_display = playbook.replace('-', ' ').title()
        status_display = status.capitalize()
        key_labels.append(f"{playbook_display} ({status_display})")
        
        # Asignar color único para esta combinación
        if (playbook, status) not in playbook_status_colors:
            base_color = playbook_base_colors[playbook]
            
            # Modificar ligeramente el color según el estado
            if status == 'successful':
                # Mantener el color base para successful
                color = base_color
            elif status == 'failed':
                # Oscurecer para failed
                color = darken_color(base_color, 0.2)
            elif status == 'running':
                # Aclarar para running
                color = lighten_color(base_color, 0.2)
            elif status == 'pending':
                # Desaturar para pending
                color = desaturate_color(base_color, 0.3)
            else:
                color = base_color
                
            playbook_status_colors[(playbook, status)] = color
        
        key_colors.append(playbook_status_colors[(playbook, status)])
    
    # Mapear claves a etiquetas y colores
    key_label_map = {key: lbl for key, lbl in zip(unique_keys, key_labels)}
    key_color_map = {key: color for key, color in zip(unique_keys, key_colors)}
    
    # Llenar los datos para el gráfico principal
    for r in records:
        key = (r['playbook_name'], r['status'])
        if key in grouped:
            date_str = r['date'].strftime('%Y-%m-%d') if isinstance(r['date'], datetime) else r['date']
            if date_str in labels:
                idx = labels.index(date_str)
                grouped[key][idx] += r['count']
    
    # Crear datasets para el gráfico principal
    datasets = []
    for i, key in enumerate(unique_keys):
        color = key_color_map[key]
        datasets.append({
            'label': key_label_map[key],
            'data': grouped[key],
            'backgroundColor': color + '80',  # Añadir transparencia
            'borderColor': color,
            'borderWidth': 2
        })
    
    # Obtener estadísticas adicionales para los paneles informativos
    total_executions = sum(r['count'] for r in records)
    success_rate = 0
    if total_executions > 0:
        successful = sum(r['count'] for r in records if r['status'] == 'successful')
        success_rate = round((successful / total_executions) * 100)
    
    # Top playbooks
    playbook_counts = defaultdict(int)
    for r in records:
        playbook_counts[r['playbook_name']] += r['count']
    
    top_playbooks = sorted(playbook_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # Distribución por sistema operativo
    os_counts = defaultdict(int)
    for r in records:
        os_counts[r['operating_system']] += r['count']
    
    # Colores vibrantes para el gráfico de dona
    os_colors = [
        '#FF5733', '#33FF57', '#3357FF', '#FF33F5', '#F5FF33', '#33FFF5', 
        '#8033FF', '#FF8033', '#33FF80', '#8080FF', '#FF8080', '#80FF80',
        '#FF2D00', '#00FF2D', '#2D00FF', '#FF002D', '#2DFF00', '#002DFF',
        '#AA00FF', '#FFAA00', '#00FFAA', '#00AAFF', '#FF00AA', '#AAFF00'
    ]
    
    # Asegurar que cada sistema operativo tenga un color único y distintivo
    os_labels = list(os_counts.keys())
    os_values = list(os_counts.values())
    os_color_map = {}
    
    for i, os_name in enumerate(os_labels):
        os_color_map[os_name] = os_colors[i % len(os_colors)]
    
    os_colors_list = [os_color_map[os_name] for os_name in os_labels]
    
    os_data = {
        'labels': os_labels,
        'data': os_values,
        'colors': os_colors_list
    }
    
    # Si es una solicitud AJAX, devolver solo los datos del gráfico
    if request.GET.get('ajax') == '1':
        from django.http import JsonResponse
        return JsonResponse({
            'labels': labels,
            'datasets': datasets,
        })
    
    context = {
        'labels': pyjson.dumps(labels),
        'datasets': pyjson.dumps(datasets),
        'total_executions': total_executions,
        'success_rate': success_rate,
        'top_playbooks': top_playbooks,
        'os_data': pyjson.dumps(os_data),
        'days': days,
        'start_date': start_date,
        'end_date': end_date
    }
    return render(request, 'dashboard/playbook_executions.html', context)


from playbooks.models import Playbook


def dashboard_view(request):
    environments_count = Environment.objects.count()
    groups_count = Group.objects.count()
    hosts_count = Host.objects.count()
    os_distribution = Host.objects.values('operating_system').annotate(count=Count('operating_system'))

    # Playbooks by type (by name convention: contains 'host' or 'group')
    playbooks_host_count = Playbook.objects.filter(name__icontains='host').count()
    playbooks_group_count = Playbook.objects.filter(name__icontains='group').count()
    # Operating systems supported by playbooks
    playbooks_os = Playbook.objects.values('operating_system').annotate(count=Count('operating_system'))

    context = {
        'environments_count': environments_count,
        'groups_count': groups_count,
        'hosts_count': hosts_count,
        'os_distribution': os_distribution,
        'playbooks_host_count': playbooks_host_count,
        'playbooks_group_count': playbooks_group_count,
        'playbooks_os': playbooks_os,
    }
    return render(request, 'dashboard/index.html', context)
