from django.shortcuts import render
from inventory.models import Environment, Group, Host
from django.db.models import Count

# Create your views here.

from playbooks.models import Playbook
from django.db.models.functions import TruncDate
from django.db.models import Count
import json

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
    
    # Crear etiquetas más limpias
    status_colors = {
        'successful': '#28a745',  # Verde
        'failed': '#dc3545',      # Rojo
        'running': '#17a2b8',     # Azul
        'pending': '#ffc107'      # Amarillo
    }
    
    key_labels = []
    key_colors = []
    
    for key in unique_keys:
        playbook, status = key
        # Formatear el nombre del playbook para que sea más legible
        playbook_display = playbook.replace('-', ' ').title()
        status_display = status.capitalize()
        key_labels.append(f"{playbook_display} ({status_display})")
        
        # Asignar color según el estado
        base_color = status_colors.get(status, '#6c757d')  # Gris por defecto
        key_colors.append(base_color)
    
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
    
    os_data = {
        'labels': list(os_counts.keys()),
        'data': list(os_counts.values()),
        'colors': ['#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b'][:len(os_counts)]
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
