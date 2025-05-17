from django.urls import path
from . import views
from . import views_scheduled
from . import views_sequential

urlpatterns = [
    path('sequential/', views_sequential.deploy_sequential, name='deploy_sequential'),
    path('sequential/history/', views_sequential.sequential_history, name='sequential_history'),
    path('host/', views.deploy_to_host, name='deploy_to_host'),
    path('group/', views.deploy_to_group, name='deploy_to_group'),
    path('schedule/host/', views_scheduled.schedule_to_host, name='schedule_to_host'),
    path('schedule/group/', views_scheduled.schedule_to_group, name='schedule_to_group'),
    path('schedule/history/', views_scheduled.scheduled_history, name='scheduled_history'),
    path('success/', views.deploy_success, name='deploy_success'),
    path('api/groups/', views.api_groups, name='api_groups'),
    path('api/hosts/', views.api_hosts, name='api_hosts'),
    path('api/playbooks/', __import__('deploy.views_api').views_api.api_playbooks, name='api_playbooks'),
    path('api/scheduled-status/', views_scheduled.api_scheduled_status, name='api_scheduled_status'),
]
