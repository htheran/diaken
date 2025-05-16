from django.http import JsonResponse
from playbooks.models import Playbook
from inventory.models import Group

def get_playbook_category(name):
    """
    Determina la categoría del playbook basado en su nombre.
    Categorías: install, configure, fix, reset, diagnose, clean
    """
    name_lower = name.lower()
    if 'install' in name_lower:
        return 'install'
    elif 'config' in name_lower or 'ssl' in name_lower:
        return 'configure'
    elif 'fix' in name_lower or 'repair' in name_lower:
        return 'fix'
    elif 'reset' in name_lower or 'restart' in name_lower:
        return 'reset'
    elif 'diagnose' in name_lower or 'test' in name_lower:
        return 'diagnose'
    elif 'clean' in name_lower or 'purge' in name_lower:
        return 'clean'
    else:
        return 'other'

def get_playbook_icon(category):
    """
    Devuelve el icono FontAwesome para cada categoría de playbook
    """
    icons = {
        'install': 'fa-download',
        'configure': 'fa-cog',
        'fix': 'fa-wrench',
        'reset': 'fa-sync',
        'diagnose': 'fa-stethoscope',
        'clean': 'fa-broom',
        'other': 'fa-file-code'
    }
    return icons.get(category, 'fa-file-code')

def get_playbook_color(category):
    """
    Devuelve el color para cada categoría de playbook
    """
    colors = {
        'install': '#28a745',  # verde
        'configure': '#007bff', # azul
        'fix': '#fd7e14',      # naranja
        'reset': '#6f42c1',    # morado
        'diagnose': '#17a2b8', # cyan
        'clean': '#dc3545',    # rojo
        'other': '#6c757d'     # gris
    }
    return colors.get(category, '#6c757d')

def api_playbooks(request):
    group_id = request.GET.get('group_id')
    host_id = request.GET.get('host_id')
    
    if host_id:
        playbooks = Playbook.objects.filter(playbook_type='host').order_by('name')
        data = []
        for pb in playbooks:
            category = get_playbook_category(pb.name)
            data.append({
                'id': pb.id, 
                'name': pb.name,
                'type': pb.playbook_type,
                'os': pb.operating_system,
                'category': category,
                'icon': get_playbook_icon(category),
                'color': get_playbook_color(category)
            })
        return JsonResponse({'playbooks': data})
    elif group_id:
        playbooks = Playbook.objects.filter(playbook_type='group').order_by('name')
        data = []
        for pb in playbooks:
            category = get_playbook_category(pb.name)
            data.append({
                'id': pb.id, 
                'name': pb.name,
                'type': pb.playbook_type,
                'os': pb.operating_system,
                'category': category,
                'icon': get_playbook_icon(category),
                'color': get_playbook_color(category)
            })
        return JsonResponse({'playbooks': data})
    else:
        playbooks_host = Playbook.objects.filter(playbook_type='host').order_by('name')
        playbooks_group = Playbook.objects.filter(playbook_type='group').order_by('name')
        
        data_host = []
        for pb in playbooks_host:
            category = get_playbook_category(pb.name)
            data_host.append({
                'id': pb.id, 
                'name': pb.name,
                'type': pb.playbook_type,
                'os': pb.operating_system,
                'category': category,
                'icon': get_playbook_icon(category),
                'color': get_playbook_color(category)
            })
            
        data_group = []
        for pb in playbooks_group:
            category = get_playbook_category(pb.name)
            data_group.append({
                'id': pb.id, 
                'name': pb.name,
                'type': pb.playbook_type,
                'os': pb.operating_system,
                'category': category,
                'icon': get_playbook_icon(category),
                'color': get_playbook_color(category)
            })
            
        return JsonResponse({'playbooks_host': data_host, 'playbooks_group': data_group})
