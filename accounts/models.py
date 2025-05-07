from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
import bcrypt

class CustomUserManager(UserManager):
    def create_superuser(self, **extra_fields):
        extra_fields.setdefault('security_phrase', bcrypt.hashpw(
            'admin-phrase'.encode(),  # Cambiar en producción
            bcrypt.gensalt()
        ).decode())
        return super().create_superuser(**extra_fields)

class CustomUser(AbstractUser):
    security_phrase = models.CharField(
        _('Frase de seguridad'),
        max_length=128,
        blank=False,
        help_text=_('Frase secreta para verificación adicional')
    )

    objects = CustomUserManager()

    def set_security_phrase(self, phrase):
        if not phrase:
            raise ValueError(_('La frase no puede estar vacía'))
        self.security_phrase = bcrypt.hashpw(
            phrase.encode(), 
            bcrypt.gensalt()
        ).decode()

    def check_security_phrase(self, phrase):
        return bcrypt.checkpw(
            phrase.encode(), 
            self.security_phrase.encode()
        )

    class Meta:
        verbose_name = _('Usuario personalizado')
        verbose_name_plural = _('Usuarios personalizados')

