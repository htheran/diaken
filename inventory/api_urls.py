from django.urls import path
from .api_views import groups_by_environment

urlpatterns = [
    path('groups-by-environment/<int:environment_id>/', groups_by_environment, name='api_groups_by_environment'),
]
