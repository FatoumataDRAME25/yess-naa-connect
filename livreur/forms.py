from django import forms
import re


class LivreurLoginForm(forms.Form):
    """
    On authentifie par téléphone, pas par 'username' au sens Django.
    La vue se charge de retrouver le username réel à partir du téléphone
    (voir authenticate() dans views.py).
    """
    telephone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'placeholder': '77 000 00 00'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': '••••••••'})
    )

    def clean_telephone(self):
        """Retire les espaces présents dans le numéro saisi."""
        telephone = self.cleaned_data['telephone']
        return re.sub(r'\s+', '', telephone)

    def clean_password(self):
        """Retire les espaces saisis dans le mot de passe du livreur."""
        password = self.cleaned_data['password']
        return re.sub(r'\s+', '', password)
