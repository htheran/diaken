from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.hashers import check_password
from .models import CustomUser

class CustomAuthBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = CustomUser.objects.get(username=username)
            if check_password(password, user.password):  # Usa el sistema de Django
                return user
        except CustomUser.DoesNotExist:
            return None

