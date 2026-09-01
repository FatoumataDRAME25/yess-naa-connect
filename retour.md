# Planification des retours clients — Projet Yess Naa Connect

> Document de planification basé sur les notes de retour de la cliente.  
> Rédigé le : 17 août 2026  
> État du projet : interface admin/transformatrice opérationnelle, espaces producteur/client/livreur partiellement implémentés.

---

## Résumé des retours à traiter

| # | Retour client | Nature | Complexité |
|---|---|---|---|
| R1 | Naming : "Riz de la Teranga" au lieu de "Riz local du Sénégal" | Contenu / UI | Faible |
| R2 | Système de remise à partir de 3 tonnes | Fonctionnel / DB | Moyenne |
| R3 | Section Publicité / vidéo n'est plus visible | UI / Bug | Faible |
| R4 | Renommer espaces : "Espace Producteurs(trices) / Espace Transformateurs(trices)" | UI / Navigation | Faible |
| R5 | Sécurité des paiements | Technique / Sécurité | Élevée |
| R6 | Protection des données personnelles (RGPD-like) | Légal / Technique | Élevée |
| R7 | Suivi de stock pour producteur et transformateur partenaires | Fonctionnel / DB | Moyenne |
| R8 | Corriger slogan : "de la rizière à la table" → "de la rizière au repas partagé" | Contenu / UI | Faible |
| R9 | Intégrer toutes les variétés de riz | Modèle / UI | Moyenne |
| R10 | Nouveau slogan à afficher | Contenu / UI | Faible |

---

## Planification détaillée par prompt

---

### PROMPT 1 — Naming & slogans (R1, R8, R10)
**Durée estimée : 15–20 min**  
**Fichiers concernés :** `templates/espace_admin/base.html`, `tracabilite.html`, `about.html`, `dashboard.html`, `stocks_producteurs.html`, `catalogue.html`

**Travaux :**
- Remplacer toutes les occurrences de "Riz Local" / "Riz local du Sénégal" par **"Riz de la Teranga"** dans les templates et le code Python
- Corriger le slogan "du champ à votre table" → **"de la rizière au repas partagé"**
- Ajouter le nouveau slogan : **"Le riz de la téranga cultivé avec soin, transformé avec amour et livré avec confiance"** dans la page À propos et/ou la landing

---

### PROMPT 2 — Visibilité de la section Publicité / Vidéo (R3)
**Durée estimée : 20–30 min**  
**Fichiers concernés :** `templates/espace_admin/about.html`, éventuellement `static/`

**Travaux :**
- Diagnostiquer pourquoi la vidéo n'est plus visible (fichier manquant, chemin cassé, balise `<video>` mal configurée)
- Corriger le chemin de la vidéo (`/static/images/DEMO%20YESS.mp4`) ou rétablir le fichier manquant
- S'assurer que la section publicité est bien visible sur mobile et desktop
- Ajouter un fallback si le fichier vidéo est absent (image statique + message explicite)

---

### PROMPT 3 — Renommage des espaces (R4)
**Durée estimée : 20–30 min**  
**Fichiers concernés :** `base.html`, `about.html`, `dashboard.html`, tout template contenant "espace producteur" ou "espace transformatrice"

**Travaux :**
- Remplacer "Espace Producteurs" par **"Espace Producteurs(trices)"**
- Remplacer "Espace Transformatrices" / "Admin Transformatrice" par **"Espace Transformateurs(trices)"**
- Mettre à jour les labels de navigation, les titres de pages et les descriptions dans tous les templates concernés

---

### PROMPT 4 — Intégration des variétés de riz (R9)
**Durée estimée : 30–45 min**  
**Fichiers concernés :** `admin/models.py`, `client/models.py`, `producteur/models.py`, `catalogue.html`, formulaire d'ajout de produit

**Travaux :**
- Mettre à jour `TYPE_CHOIX` dans `admin.Produit` et `client.Produit` pour inclure toutes les variétés :
  - Riz brisé, Riz entier, Riz étuvé, Riz aromatisé (Jasmine), Riz extra fin, Riz Basmati
- Mettre à jour `VARIETE_CHOIX` dans `producteur.StockPaddy` en conséquence
- Mettre à jour le formulaire d'ajout dans le modal du catalogue
- Créer et appliquer les migrations Django

---

### PROMPT 5 — Système de remise à partir de 3 tonnes (R2)
**Durée estimée : 45–60 min**  
**Fichiers concernés :** `admin/models.py`, `admin/views.py`, `client/models.py`, `client/views.py`, templates commande/catalogue

**Travaux :**
- Créer un modèle `RegleRemise` (seuil en kg, pourcentage ou montant de remise)
- Ajouter la logique de calcul dans le tunnel de commande client : si quantité ≥ 3 000 kg (3 tonnes), appliquer automatiquement la remise
- Afficher la remise dans le résumé de commande et la confirmation
- Permettre à l'admin de configurer le seuil et le taux de remise depuis l'espace transformatrice
- Créer et appliquer les migrations

---

### PROMPT 6 — Suivi de stock pour le partenaire (R7)
**Durée estimée : 60–90 min**  
**Fichiers concernés :** `producteur/views.py`, `producteur/models.py`, `admin/views.py`, templates producteur, templates admin

**Travaux :**
- Créer les vues et templates manquants pour l'espace producteur :
  - Dashboard producteur avec vue de son stock déclaré et statut en temps réel
  - Historique des commandes paddy passées par la transformatrice sur son stock
- Ajouter dans l'espace transformatrice une vue récapitulative par partenaire (stock acheté, restant, livré)
- Relier `StockPaddy.quantite_restante` à une UI lisible dans l'espace producteur
- Ajouter les URLs et la navigation pour l'espace producteur

---

### PROMPT 7 — Sécurité des paiements (R5)
**Durée estimée : 90–120 min**  
**Fichiers concernés :** `client/views.py`, `client/models.py`, `yessnaaconnect/settings.py`, potentiellement nouveau fichier de configuration paiement

**Travaux :**
- Intégrer un prestataire de paiement mobile Money sécurisé pour Orange Money et Wave (ex : PayDunya, CinetPay ou Paydunya SDK Sénégal)
- Implémenter les webhooks de confirmation de paiement
- Passer toutes les transactions en HTTPS (vérifier la configuration `settings.py` pour la production)
- Ajouter les en-têtes de sécurité HTTP (HSTS, CSP, X-Frame-Options déjà présent)
- Stocker les montants de façon sécurisée et ne jamais recalculer le total côté client
- Ajouter une validation serveur stricte avant toute confirmation de commande

---

### PROMPT 8 — Protection des données personnelles (R6)
**Durée estimée : 60–90 min**  
**Fichiers concernés :** `client/models.py`, templates client, `yessnaaconnect/settings.py`, potentiel nouveau template `mentions_legales.html`

**Travaux :**
- Créer une page de Politique de Confidentialité et Mentions Légales
- Ajouter un bandeau de consentement aux cookies sur la landing/catalogue client
- Chiffrer les numéros de téléphone et emails sensibles en base (ou documenter la politique de rétention des données)
- Ajouter une case à cocher consentement sur le formulaire de commande client
- Sécuriser les variables d'environnement : `SECRET_KEY`, `DEBUG=False` en prod, `ALLOWED_HOSTS` correct
- Documenter la politique de durée de conservation des données commandes/clients

---

## Récapitulatif

| Prompt | Retours couverts | Durée estimée |
|--------|-----------------|---------------|
| 1 | R1, R8, R10 — Naming & slogans | ~15–20 min |
| 2 | R3 — Vidéo/Publicité | ~20–30 min |
| 3 | R4 — Renommage espaces | ~20–30 min |
| 4 | R9 — Variétés de riz | ~30–45 min |
| 5 | R2 — Système de remise 3 tonnes | ~45–60 min |
| 6 | R7 — Suivi de stock partenaires | ~60–90 min |
| 7 | R5 — Sécurité paiements | ~90–120 min |
| 8 | R6 — Protection données personnelles | ~60–90 min |

**Total : 8 prompts — estimation totale : 6 à 9 heures de travail**

---

## Ordre d'exécution recommandé

```
Priorité haute (visibilité immédiate) :
  Prompt 1 → Prompt 3 → Prompt 2

Priorité moyenne (fonctionnel métier) :
  Prompt 4 → Prompt 5 → Prompt 6

Priorité haute (mise en production) :
  Prompt 7 → Prompt 8
```

> Les prompts 1 à 4 sont indépendants et peuvent être lancés dans n'importe quel ordre.  
> Les prompts 7 et 8 sont à traiter **avant toute mise en production**.  
> Le prompt 5 (remise) dépend du prompt 4 (variétés) pour être cohérent avec le catalogue.

---

## Notes importantes

- **Migrations** : les prompts 4, 5 et 6 nécessitent des migrations Django. Il faudra lancer `makemigrations` et `migrate` après chaque modification de modèle.
- **Données factices** : les vues `dashboard`, `commandes` et `stocks` utilisent encore des fonctions `_get_dummy_*()`. Le passage aux vraies données DB peut être intégré dans les prompts concernés si souhaité.
- **Paiement** : l'intégration réelle d'Orange Money / Wave (prompt 7) nécessite l'obtention de clés API auprès des opérateurs ou d'un agrégateur comme CinetPay/PayDunya — prévoir ce délai administratif.
- **Hébergement** : pour les prompts 7 et 8, un déploiement sur serveur HTTPS est indispensable (ex. : VPS avec Nginx + Let's Encrypt).
