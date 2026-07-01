from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


class CustomUserManager(UserManager):

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        # Fournit des valeurs par défaut pour les champs obligatoires
        extra_fields.setdefault('prenom', 'Super')
        extra_fields.setdefault('nom', 'Admin')
        extra_fields.setdefault('telephone', '0000000000')
        extra_fields.setdefault('role', 'admin')
        return super().create_superuser(username, email, password, **extra_fields)

    def create_producteur(self, username, password, **extra_fields):
        extra_fields['role'] = User.Role.PRODUCTEUR
        return self.create_user(username, password=password, **extra_fields)

    def create_livreur(self, username, password, **extra_fields):
        extra_fields['role'] = User.Role.LIVREUR
        return self.create_user(username, password=password, **extra_fields)

    def create_admin_role(self, username, password, **extra_fields):
        extra_fields['role'] = User.Role.ADMIN
        return self.create_user(username, password=password, **extra_fields)


class User(AbstractUser):
    class Role(models.TextChoices):
        PRODUCTEUR = 'producteur', 'Producteur'
        LIVREUR = 'livreur', 'Livreur'
        ADMIN = 'admin', 'Administrateur'

    prenom = models.CharField(max_length=100)
    nom = models.CharField(max_length=100)
    telephone = models.CharField(max_length=20)
    role = models.CharField(max_length=20, choices=Role.choices)
    photo = models.ImageField(upload_to='users/photos/', blank=True, null=True)
    adresse = models.CharField(max_length=255, blank=True)

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.prenom} {self.nom} ({self.get_role_display()})"