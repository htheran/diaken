from django.http import JsonResponse
from .models import Group, Environment
from django.contrib.auth.decorators import login_required

@login_required
def groups_by_environment(request, environment_id):
    """
    API para obtener los grupos que pertenecen a un ambiente específico.
    """
    try:
        # Verificar que el ambiente existe
        environment = Environment.objects.get(pk=environment_id)
        
        # Obtener los grupos que pertenecen a este ambiente
        groups = Group.objects.filter(environment=environment).order_by('name')
        
        # Formatear la respuesta
        groups_data = [{'id': group.id, 'name': group.name} for group in groups]
        
        return JsonResponse({'groups': groups_data})
    except Environment.DoesNotExist:
        return JsonResponse({'error': 'El ambiente no existe'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
