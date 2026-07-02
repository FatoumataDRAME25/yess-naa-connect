from django import forms
from administration.models import User  # adapte selon le nom de ton app

REGIONS_SENEGAL = [
    ('', 'Sélectionnez votre région'),
    ('saint-louis', 'Saint-Louis'),
    ('dakar', 'Dakar'),
    ('thies', 'Thiès'),
    ('ziguinchor', 'Ziguinchor'),
    ('kaolack', 'Kaolack'),
    ('tambacounda', 'Tambacounda'),
    ('kolda', 'Kolda'),
    ('matam', 'Matam'),
    ('louga', 'Louga'),
    ('fatick', 'Fatick'),
    ('kaffrine', 'Kaffrine'),
    ('kedougou', 'Kédougou'),
    ('sedhiou', 'Sédhiou'),
]

INPUT_CLASS = "w-full pl-10 pr-4 py-3.5 bg-[#F8FAFC] border border-slate-200 rounded-xl text-base text-slate-700 placeholder-gray-400 outline-none focus:border-green-700 transition"

class InscriptionProducteurForm(forms.Form):
    prenom = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'Ex: Moussa',
            'class': INPUT_CLASS,
        })
    )
    nom = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'Ex: Diop',
            'class': INPUT_CLASS,
        })
    )
    telephone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'placeholder': '77 000 00 00',
            'class': "w-full px-4 py-3.5 bg-[#F8FAFC] border border-slate-200 rounded-xl text-base text-slate-700 placeholder-gray-400 outline-none focus:border-green-700 transition",
        })
    )
    region = forms.ChoiceField(
        choices=REGIONS_SENEGAL,
        widget=forms.Select(attrs={
            'class': "w-full pl-10 pr-10 py-3.5 bg-[#F8FAFC] border border-slate-200 rounded-xl text-base text-slate-500 appearance-none outline-none focus:border-green-700 transition cursor-pointer",
        })
    )
    mot_de_passe = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': '••••••••',
            'class': INPUT_CLASS,
        })
    )
    confirmation = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': '••••••••',
            'class': INPUT_CLASS,
        })
    )
    cgu = forms.BooleanField(required=True, error_messages={
        'required': "Vous devez accepter les conditions d'utilisation."
    })

    def clean_telephone(self):
        telephone = self.cleaned_data.get('telephone')
        if User.objects.filter(telephone=telephone).exists():
            raise forms.ValidationError("Ce numéro de téléphone est déjà utilisé.")
        return telephone

    def clean(self):
        cleaned_data = super().clean()
        mdp = cleaned_data.get('mot_de_passe')
        confirm = cleaned_data.get('confirmation')
        if mdp and confirm and mdp != confirm:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        return cleaned_data
    

class ConnexionForm(forms.Form):
    telephone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'placeholder': '77 000 00 00',
            'class': "w-full px-4 py-4 bg-[#F8FAFC] border border-slate-200 rounded-xl text-base text-slate-700 placeholder-gray-400 outline-none focus:border-green-700 transition",
        })
    )
    mot_de_passe = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': '••••••••',
            'class': "w-full pl-10 pr-12 py-4 bg-[#F8FAFC] border border-slate-200 rounded-xl text-base text-slate-700 placeholder-gray-400 outline-none focus:border-green-700 transition",
        })
    )
    se_souvenir = forms.BooleanField(required=False)