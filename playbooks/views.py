from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Playbook
from .forms import PlaybookForm


# Create your views here.

def playbook_list(request):
    playbooks = Playbook.objects.all()
    return render(request, 'playbooks/playbook_list.html', {'playbooks': playbooks})


def playbook_upload(request):
    if request.method == 'POST':
        form = PlaybookForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('playbook_list')
    else:
        form = PlaybookForm()
    return render(request, 'playbooks/playbook_upload.html', {'form': form})


def playbook_edit(request, pk):
    playbook = Playbook.objects.get(pk=pk)
    if request.method == 'POST':
        form = PlaybookForm(request.POST, request.FILES, instance=playbook)
        if form.is_valid():
            form.save()
            return redirect('playbook_list')
    else:
        form = PlaybookForm(instance=playbook)
    return render(request, 'playbooks/playbook_edit.html', {'form': form})


def playbook_delete(request, pk):
    playbook = Playbook.objects.get(pk=pk)
    if request.method == 'POST':
        playbook.delete()
        return redirect('playbook_list')
    return render(request, 'playbooks/playbook_delete.html', {'playbook': playbook})
