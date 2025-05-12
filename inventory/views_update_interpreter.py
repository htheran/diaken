from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Host
from .update_interpreter import update_python_interpreter

def update_python_interpreter_view(request, pk):
    """
    Vista para actualizar el intérprete de Python de un host.
    """
    host = get_object_or_404(Host, pk=pk)
    
    if request.method == "POST":
        new_interpreter = request.POST.get('ansible_python_interpreter')
        if new_interpreter:
            success = update_python_interpreter(pk, new_interpreter)
            if success:
                messages.success(request, f"Intérprete de Python actualizado exitosamente a {new_interpreter}")
            else:
                messages.error(request, "Error al actualizar el intérprete de Python")
        else:
            messages.error(request, "El intérprete de Python no puede estar vacío")
        
        return redirect('host_detail', pk=pk)
    
    return render(request, 'inventory/update_interpreter.html', {'host': host})
