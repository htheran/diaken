from django.urls import path
from . import views

urlpatterns = [
    path('host/', views.deploy_to_host, name='deploy_to_host'),
    path('group/', views.deploy_to_group, name='deploy_to_group'),
    path('success/', views.deploy_success, name='deploy_success'),
    path('api/groups/', views.api_groups, name='api_groups'),
    path('api/hosts/', views.api_hosts, name='api_hosts'),
]
