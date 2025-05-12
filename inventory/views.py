from django.shortcuts import render, get_object_or_404, redirect
from .models import Environment, Group, Host
from .forms import EnvironmentForm, GroupForm, HostForm
from .views_update_interpreter import update_python_interpreter_view

# Create your views here.

# List views
def environment_list(request):
    environments = Environment.objects.all()
    return render(request, 'inventory/environment_list.html', {'environments': environments})


def group_list(request):
    groups = Group.objects.all()
    return render(request, 'inventory/group_list.html', {'groups': groups})


def host_list(request):
    hosts = Host.objects.all()
    return render(request, 'inventory/host_list.html', {'hosts': hosts})

# Detail views
def environment_detail(request, pk):
    environment = get_object_or_404(Environment, pk=pk)
    return render(request, 'inventory/environment_detail.html', {'environment': environment})


def group_detail(request, pk):
    group = get_object_or_404(Group, pk=pk)
    return render(request, 'inventory/group_detail.html', {'group': group})


def host_detail(request, pk):
    host = get_object_or_404(Host, pk=pk)
    return render(request, 'inventory/host_detail.html', {'host': host})

# Create views
def environment_create(request):
    if request.method == "POST":
        form = EnvironmentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('environment_list')
    else:
        form = EnvironmentForm()
    return render(request, 'inventory/environment_form.html', {'form': form})


def group_create(request):
    if request.method == "POST":
        form = GroupForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('group_list')
    else:
        form = GroupForm()
    return render(request, 'inventory/group_form.html', {'form': form})


def host_create(request):
    # Make ansible fields available in the form and handle saving them

    if request.method == "POST":
        form = HostForm(request.POST)
        if form.is_valid():
            host = form.save()
            # Escribir en /etc/hosts si no existe la entrada
            if host.name and host.ip:
                try:
                    with open('/etc/hosts', 'r+') as f:
                        lines = f.readlines()
                        exists = any(
                            (host.ip in l or host.name in l) and not l.strip().startswith('#')
                            for l in lines
                        )
                        if not exists:
                            f.write(f"{host.ip}\t{host.name}\n")
                except Exception as e:
                    print(f"[WARN] No se pudo escribir en /etc/hosts: {e}")
            return redirect('host_list')
    else:
        form = HostForm()
    return render(request, 'inventory/host_form.html', {'form': form})

# Update views
def environment_update(request, pk):
    environment = get_object_or_404(Environment, pk=pk)
    if request.method == "POST":
        form = EnvironmentForm(request.POST, instance=environment)
        if form.is_valid():
            form.save()
            return redirect('environment_detail', pk=pk)
    else:
        form = EnvironmentForm(instance=environment)
    return render(request, 'inventory/environment_form.html', {'form': form})


def group_update(request, pk):
    group = get_object_or_404(Group, pk=pk)
    if request.method == "POST":
        form = GroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            return redirect('group_detail', pk=pk)
    else:
        form = GroupForm(instance=group)
    return render(request, 'inventory/group_form.html', {'form': form})


def host_update(request, pk):
    host = get_object_or_404(Host, pk=pk)
    if request.method == "POST":
        form = HostForm(request.POST, instance=host)
        if form.is_valid():
            form.save()
            return redirect('host_detail', pk=pk)
    else:
        form = HostForm(instance=host)
    return render(request, 'inventory/host_form.html', {'form': form})

# Delete views
def environment_delete(request, pk):
    environment = get_object_or_404(Environment, pk=pk)
    if request.method == "POST":
        environment.delete()
        return redirect('environment_list')
    return render(request, 'inventory/environment_confirm_delete.html', {'environment': environment})


def group_delete(request, pk):
    group = get_object_or_404(Group, pk=pk)
    if request.method == "POST":
        group.delete()
        return redirect('group_list')
    return render(request, 'inventory/group_confirm_delete.html', {'group': group})


def host_delete(request, pk):
    host = get_object_or_404(Host, pk=pk)
    if request.method == "POST":
        host.delete()
        return redirect('host_list')
    return render(request, 'inventory/host_confirm_delete.html', {'host': host})
