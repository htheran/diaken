from django.shortcuts import render
from inventory.models import Environment, Group, Host
from django.db.models import Count

# Create your views here.

from playbooks.models import Playbook
from django.db.models.functions import TruncDate
from django.db.models import Count
import json

def playbook_executions_view(request):
    from collections import defaultdict
    import json as pyjson
    from django.db import connection

    raw_sql = '''
        SELECT p.name as playbook_name, p.operating_system, h.status, DATE(h.date) as date, COUNT(*) as count
        FROM history_history h
        JOIN playbooks_playbook p ON h.playbook_id = p.id
        GROUP BY p.name, p.operating_system, h.status, DATE(h.date)
        ORDER BY date;
    '''
    with connection.cursor() as cursor:
        cursor.execute(raw_sql)
        rows = cursor.fetchall()

    records = []
    for row in rows:
        records.append({
            'playbook_name': row[0],
            'operating_system': row[1],
            'status': row[2],
            'date': row[3].strftime('%Y-%m-%d'),
            'count': row[4]
        })

    counter = Counter((r['playbook_name'], r['operating_system'], r['status'], r['date']) for r in records)
    all_dates = sorted({r['date'] for r in records})
    labels = [date for date in all_dates]
    legend = []
    grouped = {}
    for (playbook, os, status, date), count in counter.items():
        key = f"{playbook} [{os}] ({status})"
        if key not in legend:
            legend.append(key)
        if key not in grouped:
            grouped[key] = [0]*len(labels)
        idx = labels.index(date)
        grouped[key][idx] = count

    color_palette = [
        'rgba(75,192,192,0.85)', 'rgba(255,99,132,0.7)', 'rgba(54,162,235,0.7)',
        'rgba(255,206,86,0.7)', 'rgba(153,102,255,0.7)', 'rgba(255,159,64,0.7)'
    ]
    datasets = []
    for i, key in enumerate(legend):
        datasets.append({
            'label': key,
            'data': grouped[key],
            'backgroundColor': color_palette[i % len(color_palette)],
            'borderColor': color_palette[i % len(color_palette)].replace('0.7', '1'),
            'borderWidth': 2
        })

    logger = logging.getLogger(__name__)
    logger.info('Playbook Executions Chart - labels: %s', labels)
    logger.info('Playbook Executions Chart - datasets: %s', datasets)

    raw_metric = [
        {
            'playbook_name': playbook_name,
            'operating_system': operating_system,
            'status': status,
            'date': date,
            'count': count
        }
        for (playbook_name, operating_system, status, date), count in counter.items()
    ]

    if request.GET.get('ajax') == '1':
        from django.http import JsonResponse
        return JsonResponse({
            'labels': labels,
            'datasets': datasets,
        })
    elif request.GET.get('debug') == '1':
        from django.http import JsonResponse
        return JsonResponse(raw_metric, safe=False)
    context = {
        'labels': pyjson.dumps(labels),
        'datasets': pyjson.dumps(datasets),
        'raw_metric': pyjson.dumps(raw_metric),
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
