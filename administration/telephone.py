import re


def normaliser_telephone(valeur):
    """
    Ramène un numéro sénégalais saisi librement à 9 chiffres :
    « 77 123 45 67 », « 77-123-45-67 », « +221 77 123 45 67 », « 00221771234567 » → « 771234567 ».
    Ne lève jamais d'erreur (utilisé pour retrouver un compte à la connexion).
    """
    chiffres = re.sub(r'\D', '', valeur or '')
    if len(chiffres) > 9 and chiffres.startswith(('00221', '221')):
        chiffres = chiffres[-9:]
    return chiffres


def trouver_par_telephone(queryset, valeur):
    """
    Retrouve l'utilisateur dont le numéro correspond, quel que soit le format
    enregistré (y compris d'anciens comptes saisis avec des espaces).
    """
    cible = normaliser_telephone(valeur)
    if len(cible) < 9:
        return None
    exact = queryset.filter(telephone=cible).first()
    if exact:
        return exact
    for user in queryset.filter(telephone__regex=r'.*' + r'\D*'.join(cible[-4:]) + r'\D*$'):
        if normaliser_telephone(user.telephone) == cible:
            return user
    return None
