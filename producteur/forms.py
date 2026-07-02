from django import forms
from administration.models import User
from producteur.models import StockPaddy

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


FIELD_CLASS = "w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg text-base text-gray-900 outline-none focus:border-[#2d5a27] focus:ring-2 focus:ring-[#2d5a27]/10 transition"

class ProfilForm(forms.ModelForm):
    region = forms.ChoiceField(
        choices=REGIONS_SENEGAL,
        label="Région",
        widget=forms.Select(attrs={'class': FIELD_CLASS}),
    )

    class Meta:
        model = User
        fields = ['prenom', 'nom', 'email', 'telephone', 'region']
        labels = {
            'prenom': 'Prénom',
            'nom': 'Nom',
            'email': 'Email',
            'telephone': 'Numéro de téléphone',
        }
        widgets = {
            'prenom':    forms.TextInput(attrs={'class': FIELD_CLASS}),
            'nom':       forms.TextInput(attrs={'class': FIELD_CLASS}),
            'email':     forms.EmailInput(attrs={'class': FIELD_CLASS}),
            'telephone': forms.TextInput(attrs={'class': FIELD_CLASS}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pré-remplir région depuis le champ adresse de l'utilisateur
        if self.instance and self.instance.adresse:
            self.fields['region'].initial = self.instance.adresse

    def save(self, commit=True):
        user = super().save(commit=False)
        # Stocker la région dans le champ adresse
        user.adresse = self.cleaned_data.get('region', '')
        if commit:
            user.save()
        return user



class DeclarationPaddyForm(forms.ModelForm):
    region = forms.ChoiceField(
        choices=REGIONS_SENEGAL,
        label="Région de production",
        widget=forms.Select(attrs={
            'class': "w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg text-base text-green-brand appearance-none outline-none focus:border-green-accent focus:ring-2 focus:ring-green-accent/10 transition cursor-pointer",
        }),
    )

    class Meta:
        model = StockPaddy
        fields = ['photo', 'variete', 'quantite_kg', 'date_recolte', 'region', 'prix_par_kg', 'description', 'est_bio']
        labels = {
            'photo':        'Photo de la récolte',
            'variete':      'Variété de riz',
            'quantite_kg':  'Quantité disponible (kg)',
            'date_recolte': 'Date de récolte',
            'prix_par_kg':  'Prix proposé (FCFA/kg)',
            'description':  'Particularités de votre récolte (optionnel)',
            'est_bio':      'Récolte biologique (BIO)',
        }
        widgets = {
            'photo': forms.ClearableFileInput(attrs={
                'class': "hidden",
                'accept': "image/jpeg,image/png",
                'id': 'id_photo',
            }),

            'variete': forms.Select(attrs={
                'class': "w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg text-base text-green-brand appearance-none outline-none focus:border-green-accent focus:ring-2 focus:ring-green-accent/10 transition cursor-pointer",
            }),
            'quantite_kg': forms.NumberInput(attrs={
                'class': "flex-1 text-center py-3 bg-transparent text-base font-medium text-green-brand outline-none",
                'min': '1',
                'id': 'id_quantite_kg',
            }),
            'date_recolte': forms.DateInput(attrs={
                'type': 'date',
                'class': "w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg text-base text-green-brand outline-none focus:border-green-accent focus:ring-2 focus:ring-green-accent/10 transition",
            }),
            'prix_par_kg': forms.NumberInput(attrs={
                'class': "w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg text-base font-semibold text-green-brand outline-none focus:border-green-accent focus:ring-2 focus:ring-green-accent/10 transition pr-24",
                'min': '1',
                'step': '1',
            }),

             'description': forms.Textarea(attrs={
                'class': "w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg text-base placeholder-gray-400 outline-none focus:border-green-700 transition resize-none",
                'rows': '4',
                'placeholder': "Ex: Grains très longs, récolte sous abri, faible taux d'humidité...",
                'required': False,
            }),
            'est_bio': forms.CheckboxInput(attrs={
                'class': "w-4 h-4 rounded border-gray-300 text-green-brand focus:ring-green-accent cursor-pointer",
            }),
        }


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # photo obligatoire
        self.fields['photo'].required = True
        # description optionnelle
        self.fields['description'].required = False


    def clean_quantite_kg(self):
        val = self.cleaned_data.get('quantite_kg')
        if val is not None and val <= 0:
            raise forms.ValidationError("La quantité doit être supérieure à 0.")
        return val

    def clean_prix_par_kg(self):
        val = self.cleaned_data.get('prix_par_kg')
        if val is not None and val <= 0:
            raise forms.ValidationError("Le prix doit être supérieur à 0.")
        return val
