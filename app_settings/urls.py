from django.urls import path
from . import views

urlpatterns = [
    path('global/', views.global_setting_list, name='global_setting_list'),
    path('global/new/', views.global_setting_create, name='global_setting_create'),
    path('global/<int:pk>/edit/', views.global_setting_update, name='global_setting_update'),
    path('credentials/', views.credential_list, name='credential_list'),
    path('credentials/new/', views.credential_create, name='credential_create'),
    path('credentials/<int:pk>/edit/', views.credential_update, name='credential_update'),
]
