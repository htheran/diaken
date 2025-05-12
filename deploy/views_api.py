from django.http import JsonResponse
from playbooks.models import Playbook
from inventory.models import Group

def api_playbooks(request):
    group_id = request.GET.get('group_id')
    host_id = request.GET.get('host_id')
    if host_id:
        playbooks = Playbook.objects.filter(playbook_type='host').order_by('name')
        data = [{'id': pb.id, 'name': pb.name} for pb in playbooks]
        return JsonResponse({'playbooks': data})
    elif group_id:
        playbooks = Playbook.objects.filter(playbook_type='group').order_by('name')
        data = [{'id': pb.id, 'name': pb.name} for pb in playbooks]
        return JsonResponse({'playbooks': data})
    else:
        playbooks_host = Playbook.objects.filter(playbook_type='host').order_by('name')
        playbooks_group = Playbook.objects.filter(playbook_type='group').order_by('name')
        data_host = [{'id': pb.id, 'name': pb.name} for pb in playbooks_host]
        data_group = [{'id': pb.id, 'name': pb.name} for pb in playbooks_group]
        return JsonResponse({'playbooks_host': data_host, 'playbooks_group': data_group})
