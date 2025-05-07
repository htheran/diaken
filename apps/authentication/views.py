from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .forms import LoginForm  # Asumiendo que tienes un formulario personalizado

def custom_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                return redirect('index')
            else:
                messages.error(request, 'Credenciales inválidas')
        else:
            messages.error(request, 'Error en el formulario')
    else:
        form = LoginForm()
    
    return render(request, 'registration/login.html', {'form': form})

