from django.http import HttpResponse, HttpRequest
from django.shortcuts import render
from django.utils import timezone
from inventory.models import Host, Environment, Group

def descargar_inventario_ansible(request: HttpRequest):
    """
    Vista para descargar el inventario de Ansible en formato de texto plano.
    Incluye filtros por entorno, grupo y sistema operativo.
    """
    # Filtros avanzados
    env_id = request.GET.get('environment')
    group_id = request.GET.get('group')
    os_filter = request.GET.get('operating_system')
    
    # Aplicar filtros
    hosts = Host.objects.select_related('environment', 'group', 'deployment_credential').all()
    if env_id:
        hosts = hosts.filter(environment_id=env_id)
    if group_id:
        hosts = hosts.filter(group_id=group_id)
    if os_filter:
        hosts = hosts.filter(operating_system=os_filter)

    # Agrupación por entorno y grupo
    grouped = {}
    for host in hosts:
        env = host.environment.name if host.environment else 'Sin_Entorno'
        grp = host.group.name if host.group else 'Sin_Grupo'
        grouped.setdefault(env, {}).setdefault(grp, []).append(host)

    # Generar inventario agrupado
    lines = ["# Inventario Ansible generado automáticamente"]
    lines.append("# Fecha: " + timezone.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    # Agregar información de filtros aplicados
    if env_id or group_id or os_filter:
        lines.append("# Filtros aplicados:")
        if env_id:
            env_name = Environment.objects.filter(id=env_id).first()
            lines.append(f"# - Entorno: {env_name.name if env_name else env_id}")
        if group_id:
            group_name = Group.objects.filter(id=group_id).first()
            lines.append(f"# - Grupo: {group_name.name if group_name else group_id}")
        if os_filter:
            os_display = dict(Host.OPERATING_SYSTEM_CHOICES).get(os_filter, os_filter)
            lines.append(f"# - Sistema Operativo: {os_display}")
        lines.append("")
    
    # Generar grupos de inventario
    for env, groups in sorted(grouped.items()):
        lines.append(f"\n# Entorno: {env}")
        lines.append(f"[{env}:children]")
        for grp in sorted(groups.keys()):
            lines.append(f"{env}_{grp}")
        
        for grp, hosts_in_group in sorted(groups.items()):
            group_name = f"{env}_{grp}".replace(" ", "_")
            lines.append(f"\n# Grupo: {grp}")
            lines.append(f"[{group_name}]")
            
            for host in hosts_in_group:
                if not host.deployment_credential:
                    lines.append(f"# {host.name} - Sin credenciales configuradas")
                    continue
                    
                vars_list = [
                    f"ansible_host={host.ip}",
                    f"ansible_user={host.ansible_user or host.deployment_credential.user}",
                    f"ansible_ssh_private_key_file={host.ansible_ssh_private_key_file or ''}",
                    f"ansible_ssh_common_args='{host.ansible_ssh_common_args or ''}'",
                ]
                
                if host.operating_system == "Windows":
                    password = host.deployment_credential.get_windows_password() or ""
                    vars_list.extend([
                        "ansible_connection=ssh",
                        "ansible_port=22",
                        f"ansible_password={password}",
                        f"ansible_shell_type={host.ansible_shell_type or 'powershell'}"
                    ])
                else:
                    vars_list.append(f"ansible_python_interpreter={host.ansible_python_interpreter or 'auto'}")
                
                # Unir todas las variables en una línea
                line = f"{host.name} " + " ".join([v for v in vars_list if v.strip()])
                lines.append(line)
    
    # Unir todas las líneas y crear la respuesta
    content = '\n'.join(lines)
    filename = f"inventario_ansible_{timezone.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    response = HttpResponse(content, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from django.db.models import Q

def host_list_with_filters(request: HttpRequest):
    # Obtener todos los datos necesarios para los filtros
    environments = Environment.objects.all()
    groups = Group.objects.all().order_by('name')
    os_choices = Host.OPERATING_SYSTEM_CHOICES
    
    # Obtener parámetros de búsqueda
    search_query = request.GET.get('q', '').strip()
    
    # Iniciar la consulta con select_related para optimizar
    hosts = Host.objects.select_related('environment', 'group')
    
    # Aplicar búsqueda si existe
    if search_query:
        # Limpiar la consulta de búsqueda y convertir a minúsculas para comparación insensible a mayúsculas
        search_terms = [term.strip().lower() for term in search_query.split() if term.strip()]
        
        if search_terms:
            # Crear una consulta OR para todos los términos de búsqueda
            combined_query = Q()
            
            for term in search_terms:
                # Búsqueda en campos directos del host
                term_query = Q()
                for field in ['name', 'ip', 'description', 'ansible_user', 'ansible_python_interpreter']:
                    term_query |= Q(**{f'{field}__icontains': term})
                
                # Búsqueda en campos relacionados
                term_query |= Q(environment__name__icontains=term)
                term_query |= Q(group__name__icontains=term)
                
                # Búsqueda por sistema operativo
                for os_key, os_name in Host.OPERATING_SYSTEM_CHOICES:
                    if term in os_name.lower() or term == os_key.lower():
                        term_query |= Q(operating_system=os_key)
                
                # Agregar el término a la consulta combinada con OR
                combined_query |= term_query
            
            # Crear una consulta vacía
            query = Q()
            
            # Para el término de búsqueda completo (sin dividir)
            full_search = search_query.strip().lower()
            
            # Si el término de búsqueda tiene más de 2 caracteres
            if len(full_search) > 2:
                # Búsqueda en campos clave (coincidencia parcial)
                for field in ['name', 'ip', 'description', 'ansible_user', 'ansible_python_interpreter']:
                    query |= Q(**{f'{field}__icontains': full_search})
                
                # Búsqueda en relaciones
                query |= Q(environment__name__icontains=full_search)
                query |= Q(group__name__icontains=full_search)
                
                # Búsqueda por sistema operativo (coincidencia exacta o parcial)
                query |= Q(operating_system__iexact=full_search)
                if len(full_search) > 5:  # Para nombres de SO más largos
                    query |= Q(operating_system__icontains=full_search)
            else:
                # Para términos cortos, solo búsqueda exacta
                query = Q(name__iexact=full_search) | Q(ip__iexact=full_search)
            
            # Aplicar el filtro
            if query:
                hosts = hosts.filter(query).distinct()
            
            # Depuración: imprimir la consulta SQL generada
            print(f"Búsqueda: '{full_search}' - Consulta:", str(hosts.query) if query else "Sin consulta")
    
    # Ordenar los resultados
    # Primero por si el grupo es de Windows (para que vayan al final)
    # Luego por nombre de grupo y finalmente por nombre de host
    from django.db.models import Case, When, Value, BooleanField
    
    # Añadir anotación para ordenar grupos de Windows al final
    hosts = hosts.annotate(
        is_windows=Case(
            When(group__name__icontains='windows', then=Value(1)),
            default=Value(0),
            output_field=BooleanField()
        )
    ).order_by('is_windows', 'group__name', 'name')
    
    # Depuración: imprimir la consulta SQL generada
    print("Consulta SQL final:", str(hosts.query))
    
    # Manejar la paginación
    per_page = min(int(request.GET.get('per_page', 25)), 100)  # Límite de 100 por página
    page = request.GET.get('page', 1)
    paginator = Paginator(hosts, per_page)
    
    try:
        hosts_paginated = paginator.page(page)
        # Agregar índices de inicio y fin para el contador
        hosts_paginated.start_index = (hosts_paginated.number - 1) * paginator.per_page + 1
        hosts_paginated.end_index = min(hosts_paginated.number * paginator.per_page, paginator.count)
    except PageNotAnInteger:
        # Si el número de página no es un entero, mostrar la primera página
        hosts_paginated = paginator.page(1)
    except EmptyPage:
        # Si la página está fuera de rango, mostrar la última página
        hosts_paginated = paginator.page(paginator.num_pages)
    
    # Preparar el contexto con todos los datos necesarios
    context = {
        'hosts': hosts_paginated,
        'environments': environments,
        'groups': groups,
        'os_choices': os_choices,
        'search_query': search_query,
        'per_page': per_page
    }
    
    return render(request, 'inventory/host_list.html', context)
