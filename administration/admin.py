from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        'username',
        'prenom',
        'nom',
        'telephone',
        'role',
        'is_staff',
        'is_active',
    )

    list_filter = ('role', 'is_staff', 'is_active')

    search_fields = ('username', 'prenom', 'nom', 'telephone')

    ordering = ('username',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Informations personnelles', {
            'fields': ('prenom', 'nom', 'telephone', 'adresse', 'photo')
        }),
        ('Rôle', {
            'fields': ('role',)
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Dates importantes', {
            'fields': ('last_login', 'date_joined')
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username',
                'prenom',
                'nom',
                'telephone',
                'role',
                'password1',
                'password2',
                'is_staff',
                'is_active',
            ),
        }),
    )