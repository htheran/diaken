from django.http import HttpResponse, HttpRequest
from django.shortcuts import render
from inventory.models import Host, Environment, Group

def descargar_inventario_ansible(request: HttpRequest):
    # Filtros avanzados
    env_id = request.GET.get('environment')
    group_id = request.GET.get('group')
    os_filter = request.GET.get('operating_system')
    hosts = Host.objects.all()
    if env_id:
        hosts = hosts.filter(environment_id=env_id)
    if group_id:
        hosts = hosts.filter(group_id=group_id)
    if os_filter:
        hosts = hosts.filter(operating_system=os_filter)

    # Agrupación por entorno y grupo
    grouped = {}
    for host in hosts:
        env = host.environment.name if host.environment else 'Sin Entorno'
        grp = host.group.name if host.group else 'Sin Grupo'
        grouped.setdefault(env, {}).setdefault(grp, []).append(host)

    # Generar inventario agrupado
    lines = []
    for env, groups in grouped.items():
        lines.append(f"[{env}]")
        for grp, hosts_in_group in groups.items():
            lines.append(f"# Grupo: {grp}")
            for host in hosts_in_group:
                cred = host.deployment_credential
                if not cred:
                    continue
                if host.operating_system == "Windows":
                    password = cred.get_windows_password() or ""
                    line = (
                        f"{host.name} ansible_host={host.ip} "
                        f"ansible_connection=winrm ansible_port=5986 "
                        f"ansible_user={cred.user} "
                        f"ansible_password={password} "
                        f"ansible_winrm_server_cert_validation=ignore"
                    )
                else:
                    line = (
                        f"{host.name} ansible_host={host.ip} "
                        f"ansible_user={cred.user} "
                        # f"ansible_ssh_private_key_file=<ruta temporal> "  # La app ahora almacena la llave cifrada, se debe exportar a archivo temporal si se requiere.
                        f"ansible_python_interpreter={host.ansible_python_interpreter}"
                    )
                lines.append(line)
            lines.append("")
    content = '\n'.join(lines)
    response = HttpResponse(content, content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename="inventario_ansible.txt"'
    return response

def host_list_with_filters(request: HttpRequest):
    environments = Environment.objects.all()
    groups = Group.objects.all()
    os_choices = Host.OPERATING_SYSTEM_CHOICES
    env_id = request.GET.get('environment')
    group_id = request.GET.get('group')
    os_filter = request.GET.get('operating_system')
    hosts = Host.objects.all()
    if env_id:
        hosts = hosts.filter(environment_id=env_id)
    if group_id:
        hosts = hosts.filter(group_id=group_id)
    if os_filter:
        hosts = hosts.filter(operating_system=os_filter)
    return render(request, 'inventory/host_list.html', {
        'hosts': hosts,
        'environments': environments,
        'groups': groups,
        'os_choices': os_choices,
        'env_id': env_id,
        'group_id': group_id,
        'os_filter': os_filter,
    })
