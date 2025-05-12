from django.shortcuts import render
from .models import History

# Create your views here.

from django.core.paginator import Paginator

def history_list(request):
    histories = History.objects.all().order_by('-date')
    paginator = Paginator(histories, 10)  # 10 por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'history/history_list.html', {'page_obj': page_obj})


def history_detail(request, pk):
    history = History.objects.get(pk=pk)
    return render(request, 'history/history_detail.html', {'history': history})
