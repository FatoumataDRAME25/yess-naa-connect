# Roadmap — Riz Local
## Ce qu'il reste pour que l'application soit complète et effective à l'échelle nationale

---

## 🔴 Priorité 1 — Avant le lancement (bloquant)

Ces éléments sont indispensables. Sans eux, l'application ne peut pas fonctionner en production.

### 1. Déploiement VPS + nom de domaine
- Acheter un VPS (minimum 2 Go RAM) et un nom de domaine chez LWS
- Configurer Nginx + Gunicorn + PostgreSQL + SSL
- Toutes les étapes sont documentées dans `DEPLOIEMENT.md`

### 2. SMS de confirmation de commande
- Au Sénégal, beaucoup de clients n'ont pas d'email
- Le SMS avec le numéro `YEES-xxxx` est la seule preuve de commande fiable
- Service recommandé : **AfricasTalking** (supporte les numéros +221)
- Nécessite la création d'un compte + crédits SMS
- À implémenter dès que le compte est disponible

### 3. Vrais produits + vraies photos
- Le catalogue tourne actuellement avec des données de test
- Remplir avec les vrais produits, les vraies photos, les vrais prix avant ouverture
- Modifier les textes génériques dans les templates (À propos, accueil, etc.)

### 4. Vrais comptes utilisateurs
- Les producteurs doivent s'inscrire via `/producteur/`
- Les livreurs doivent être créés par l'admin via l'espace admin
- Créer le compte admin principal via `python manage.py createsuperuser`

---

## 🟡 Priorité 2 — Dans le mois suivant le lancement

Ces éléments sont importants pour la croissance et la confiance des utilisateurs.

### 5. SEO + Open Graph (partage WhatsApp/Facebook)
- Ajouter les balises meta Open Graph dans les templates
- Quand un lien est partagé sur WhatsApp, une belle vignette s'affiche (photo + titre + description)
- WhatsApp est le canal de partage numéro 1 au Sénégal — impact direct sur les ventes
- Travail estimé : 2-3 heures

### 6. Paiement mobile money (Wave / Orange Money)
- Actuellement seul le paiement à la livraison fonctionne vraiment
- L'absence de paiement en ligne est un frein à l'achat pour les clients éloignés
- Intégrer **Wave** (très populaire au Sénégal) ou **Orange Money**
- Nécessite un compte marchand Wave ou Orange Money Business

### 7. Zone de livraison
- Actuellement aucune restriction géographique dans le formulaire de commande
- Si la livraison ne couvre que certaines villes (Dakar, Thiès, Mbour...), il faut :
  - L'indiquer clairement sur le site
  - Ajouter un sélecteur de ville avec validation
  - Bloquer ou avertir les commandes hors zone

### 8. Formulaire de contact
- Permettre aux visiteurs de poser des questions sans passer par une commande
- Page À propos → ajouter un formulaire (nom, téléphone, message)
- Les messages arrivent par email ou sont visibles dans l'espace admin

---

## 🟠 Priorité 3 — Confiance et sécurité juridique

### 9. Conditions générales de vente (CGV) + Politique de confidentialité
- Obligatoire légalement dès qu'on collecte des données personnelles
- Les données collectées : nom, téléphone, adresse, coordonnées GPS
- Une page simple avec les CGV suffit pour démarrer
- Ajouter le lien dans le footer

### 10. Remplacement des témoignages fictifs
- Les témoignages de la section "Ils nous font confiance" sont actuellement fictifs
- Les remplacer par de vrais avis clients après les premières livraisons
- Ajouter un mécanisme simple pour recueillir les retours (par SMS ou formulaire)

### 11. Sauvegarde automatique de la base de données
- Un cron job sur le VPS qui sauvegarde PostgreSQL toutes les nuits
- Sans sauvegarde, une panne serveur = perte de toutes les commandes et données
- Commande à planifier sur le VPS :
```bash
# Exemple cron — tous les jours à 2h du matin
0 2 * * * pg_dump rizlocal_db > /backups/rizlocal_$(date +\%Y\%m\%d).sql
```

---

## 🟢 Priorité 4 — Après stabilisation (croissance)

Ces éléments peuvent attendre mais contribuent à la montée en échelle.

### 12. Application mobile (PWA ou React Native)
- Android domine largement au Sénégal
- Une PWA (Progressive Web App) permettrait d'installer l'appli depuis Chrome sans passer par le Play Store
- React Native pour une vraie app mobile si le budget le permet

### 13. Tableau de bord analytics avancé
- Voir d'où viennent les commandes (par région)
- Quels produits se vendent le plus
- Pics de commandes (jours, heures)
- Revenus par livreur
- Peut être fait avec Chart.js (déjà installé) ou intégré à Google Analytics

### 14. Système de fidélité / parrainage
- Code de parrainage pour les clients qui recommandent la plateforme
- Réduction sur la prochaine commande
- Encourager le bouche-à-oreille — très efficace au Sénégal

### 15. Notifications push navigateur
- Alerter les clients quand leur commande est en livraison
- Fonctionne sur mobile via les Service Workers (PWA)
- Pas besoin d'application installée

---

## Résumé des priorités

| Priorité | Éléments | Statut |
|----------|----------|--------|
| 🔴 Avant lancement | VPS + domaine, SMS, vrais produits, vrais comptes | À faire |
| 🟡 Mois 1 | SEO/Open Graph, Wave/Orange Money, zones de livraison, contact | À planifier |
| 🟠 Confiance | CGV, vrais témoignages, sauvegardes auto | À planifier |
| 🟢 Croissance | PWA mobile, analytics avancé, fidélité, push notifications | Plus tard |

---

## Ce qui est déjà fait ✅

- Vitrine publique (accueil, catalogue, détail produit)
- Panier en session + commande client
- Suivi de commande par numéro + téléphone
- Traçabilité QR code (du producteur au client)
- Espace admin complet (dashboard, stocks, catalogue, commandes, livreurs)
- Espace producteur (inscription, déclaration paddy, commandes reçues)
- Espace livreur (dashboard, confirmation livraison)
- Notifications temps réel sur le dashboard admin
- Modification de profil admin
- Reçu PDF téléchargeable
- Page 404 personnalisée
- Recherche de produits dans la navbar
- Déploiement documenté (DEPLOIEMENT.md)
- Base de données PostgreSQL configurée
- HTTPS + sécurité production prête
