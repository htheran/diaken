from django.urls import path
from . import views

urlpatterns = [
    path('', views.status_view, name='tools_status'),
    path('status/', views.status_view, name='tools_status'),
    path('api/check-service-status/', views.check_service_status, name='check_service_status'),
    path('api/groups/', views.api_groups, name='tools_api_groups'),
    path('api/hosts/', views.api_hosts, name='tools_api_hosts'),
]
