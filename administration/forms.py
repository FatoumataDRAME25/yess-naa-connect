from django import forms

from administration.models import User

INPUT_CLASS = (
    "w-full px-4 py-3 border border-gray-200 rounded-xl text-sm "
    "focus:outline-none focus:ring-2 focus:ring-yn-green"
)


class LivreurCreationForm(forms.Form):
    """
    Formulaire utilisé par la transformatrice/admin pour créer un compte
    livreur. Le livreur ne s'inscrit jamais lui-même : c'est l'admin qui
    lui fournit son numéro (identifiant de connexion) et son mot de passe.
    """
    prenom = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Ex: Moussa'})
    )
    nom = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Ex: Diop'})
    )
    telephone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': '77 000 00 00'})
    )
    adresse = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Zone de livraison (optionnel)'})
    )
    mot_de_passe = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': INPUT_CLASS, 'placeholder': '••••••••'})
    )

    def clean_telephone(self):
        telephone = self.cleaned_data.get('telephone', '').strip()
        if User.objects.filter(telephone=telephone).exists():
            raise forms.ValidationError("Ce numéro de téléphone est déjà utilisé par un compte existant.")
        return telephone

    def clean_mot_de_passe(self):
        mdp = self.cleaned_data.get('mot_de_passe', '')
        if len(mdp) < 6:
            raise forms.ValidationError("Le mot de passe doit contenir au moins 6 caractères.")
        return mdp
