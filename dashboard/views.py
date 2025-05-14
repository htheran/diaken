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
    
    # Get data for the last 30 days only
    thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    raw_sql = f'''
        SELECT p.name as playbook_name, p.operating_system, h.status, DATE(h.date) as date, COUNT(*) as count
        FROM history_history h
        JOIN playbooks_playbook p ON h.playbook_id = p.id
        WHERE DATE(h.date) >= '{thirty_days_ago}'
        GROUP BY p.name, p.operating_system, h.status, DATE(h.date)
        ORDER BY date DESC;
    '''
    with connection.cursor() as cursor:
        cursor.execute(raw_sql)
        rows = cursor.fetchall()

    records = []
    for row in rows:
        # Incluir todos los registros, incluso con recuento 0 para mantener continuidad
        # Los valores cero ayudan a mantener la estructura y contexto temporal
        records.append({
            'playbook_name': row[0],
            'operating_system': row[1],
            'status': row[2],
            'date': row[3],
            'count': row[4]
        })

    # Si no hay datos, crear datos de muestra
    if not records:
        # Crear algunas fechas de ejemplo para mostrar
        from datetime import datetime, timedelta
        today = datetime.now().date()
        sample_dates = [today - timedelta(days=2), today - timedelta(days=1), today]
        sample_dates_str = [d.strftime('%Y-%m-%d') for d in sample_dates]
        
        # Crear un registro de muestra para que se vea al menos una barra
        sample_record = {
            'playbook_name': 'Sample-Playbook',
            'operating_system': 'Demo',
            'status': 'successful',
            'date': today.strftime('%Y-%m-%d'),
            'count': 1  # Al menos un valor positivo
        }
        records.append(sample_record)
        
        # Log para depuración
        logger = logging.getLogger(__name__)
        logger.info('No hay datos reales. Creando datos de muestra: %s', sample_record)

    # Agrupa por combinación única de playbook+SO+status y cuenta ejecuciones por fecha
    all_dates = sorted({r['date'] for r in records})
    labels = all_dates
    
    # Generar claves únicas solo a partir de registros con count > 0
    unique_keys = sorted({(r['playbook_name'], r['operating_system'], r['status']) for r in records})
    
    # Inicializar el agrupamiento
    grouped = {key: [0]*len(labels) for key in unique_keys}
    
    # Generar etiquetas más claras para la leyenda
    key_labels = []
    status_icons = {'successful': '✅', 'failed': '❌', 'warning': '⚠️', 'pending': '⏳', 'running': '⚙️'}
    for key in unique_keys:
        playbook, os, status = key
        status_icon = status_icons.get(status.lower(), '')
        # Acortar nombres largos
        if len(playbook) > 20:
            playbook = playbook[:17] + '...'
        key_labels.append(f"{status_icon} {playbook} [{os}]")
    
    key_label_map = {key: lbl for key, lbl in zip(unique_keys, key_labels)}
    
    # Llenar datos
    for r in records:
        key = (r['playbook_name'], r['operating_system'], r['status'])
        idx = labels.index(r['date'])
        grouped[key][idx] = r['count']
    
    # Paleta de colores moderna
    color_palette = [
        'rgba(0,123,255,0.85)',    # Azul Bootstrap
        'rgba(220,53,69,0.85)',    # Rojo Bootstrap
        'rgba(40,167,69,0.85)',    # Verde Bootstrap
        'rgba(255,193,7,0.85)',    # Amarillo Bootstrap
        'rgba(111,66,193,0.85)',   # Morado Bootstrap
        'rgba(23,162,184,0.85)',   # Cian Bootstrap
        'rgba(255,99,132,0.85)',   # Rosa
        'rgba(54,162,235,0.85)',    # Azul claro
        'rgba(255,159,64,0.85)',   # Naranja
        'rgba(75,192,192,0.85)',    # Turquesa
        'rgba(153,102,255,0.85)',   # Púrpura
        'rgba(201,203,207,0.85)'    # Gris
    ]
    
    # Crear datasets con datos NO-CERO
    datasets = []
    for i, key in enumerate(unique_keys):
        # Verificar si hay al menos un valor no-cero
        if any(grouped[key]):
            datasets.append({
                'label': key_label_map[key],
                'data': grouped[key],
                'backgroundColor': color_palette[i % len(color_palette)],
                'borderColor': color_palette[i % len(color_palette)].replace('0.85', '1'),
                'borderWidth': 2
            })

    logger = logging.getLogger(__name__)
    logger.info('Playbook Executions Chart - labels: %s', labels)
    logger.info('Playbook Executions Chart - datasets: %s', datasets)

    if request.GET.get('ajax') == '1':
        from django.http import JsonResponse
        return JsonResponse({
            'labels': labels,
            'datasets': datasets,
        })
    context = {
        'labels': pyjson.dumps(labels),
        'datasets': pyjson.dumps(datasets),
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
