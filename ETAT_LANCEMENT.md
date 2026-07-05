# État au lancement — Riz Local
## Ce qui fonctionne dès l'achat du VPS et du nom de domaine

---

## Réponse courte

**Oui.** Dès que le VPS et le nom de domaine sont achetés et configurés,
l'application est fonctionnelle et peut recevoir de vraies commandes.

---

## Ce que chaque acteur peut faire dès le lancement

### 🛒 Clients (visiteurs du site)
- Parcourir le catalogue de riz local
- Filtrer les produits par type (blanc, étuvé, parfumé) et par poids (5kg, 10kg, 25kg)
- Voir le détail de chaque produit avec sa fiche de traçabilité
- Ajouter des produits au panier
- Passer une commande (nom, téléphone, adresse de livraison + GPS optionnel)
- Recevoir un numéro de commande unique (ex: `YEES-2026-A3F7`)
- Suivre l'état de leur commande via `/suivreCommande/` avec numéro + téléphone
- Scanner le QR code sur l'emballage pour voir l'origine du riz (producteur, région, variété)
- Télécharger leur reçu en PDF
- Vérifier un code lot manuellement sur `/verification/`

### ⚙️ Admin / Transformatrice
- Se connecter à l'espace admin avec téléphone ou username
- Voir le tableau de bord avec les statistiques du jour (commandes, CA, stocks)
- Recevoir des notifications en temps réel quand une nouvelle commande arrive
- Gérer le catalogue de produits (créer, modifier, supprimer)
- Consulter et traiter les commandes clients
- Assigner un livreur à une commande
- Changer le statut des commandes (attente → préparation → livraison → livrée)
- Gérer les comptes livreurs
- Commander du paddy auprès des producteurs
- Voir les stocks disponibles par producteur et par région
- Télécharger le QR code de chaque produit pour l'imprimer sur l'emballage
- Modifier son profil (nom, photo, mot de passe)

### 🌾 Producteurs
- S'inscrire sur la plateforme via `/producteur/`
- Se connecter avec leur numéro de téléphone
- Déclarer leurs récoltes de paddy (variété, quantité, prix, région)
- Recevoir les commandes paddy de l'admin
- Accepter ou refuser une commande paddy
- Consulter l'historique de leurs récoltes et commandes
- Modifier leur profil

### 🛵 Livreurs
- Se connecter avec leur numéro de téléphone (compte créé par l'admin)
- Voir leurs livraisons du jour sur le dashboard
- Consulter le détail de chaque livraison (adresse, lien Google Maps)
- Confirmer une livraison et enregistrer le montant encaissé
- Voir leur profil

---

## Ce qui manque au lancement mais ne bloque pas les commandes

| Fonctionnalité | Impact | Alternative disponible |
|----------------|--------|------------------------|
| SMS de confirmation | Le client ne reçoit pas de SMS | Le numéro de commande s'affiche à l'écran, le client peut le noter |
| Paiement Wave / Orange Money | Pas de paiement en ligne | Paiement à la livraison fonctionne |
| Vraies photos produits | Visuellement moins professionnel | À remplacer avant ouverture via l'espace admin |
| Formulaire de contact | Pas de formulaire sur À propos | Le téléphone et l'email sont affichés |

---

## Flux complet d'une commande au lancement

```
1. Client visite le site → parcourt le catalogue
2. Ajoute au panier → saisit son nom, téléphone, adresse
3. Commande enregistrée → numéro YEES-xxxx affiché + reçu PDF téléchargeable
4. Admin reçoit une notification sur le dashboard
5. Admin assigne un livreur → commande passe en "En livraison"
6. Livreur voit la livraison sur son dashboard → se rend à l'adresse
7. Livreur confirme → commande passe en "Livrée"
8. Client peut suivre l'état à tout moment via /suivreCommande/
```

---

## Conclusion

L'application couvre l'intégralité du flux métier :
de la déclaration de récolte du producteur jusqu'à la livraison au client final,
avec traçabilité complète via QR code à chaque étape.

**Action suivante : acheter le VPS + nom de domaine sur LWS et suivre le guide `DEPLOIEMENT.md`.**
