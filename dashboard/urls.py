from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('playbook-executions/', views.playbook_executions_view, name='playbook_executions'),
]
