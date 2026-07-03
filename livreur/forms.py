from django import forms


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
