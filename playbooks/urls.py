from django.urls import path
from . import views

urlpatterns = [
    path('', views.playbook_list, name='playbook_list'),
    path('host/', views.playbook_list_host, name='playbook_list_host'),
    path('group/', views.playbook_list_group, name='playbook_list_group'),
    path('upload/', views.playbook_upload, name='playbook_upload'),
    path('edit/<int:pk>/', views.playbook_edit, name='playbook_edit'),
    path('delete/<int:pk>/', views.playbook_delete, name='playbook_delete'),
]
