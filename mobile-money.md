# Intégration du Paiement Mobile Money — Yeesnaa.com
## Guide explicatif 

---

## Contexte

Actuellement sur Yeesnaa, les clients peuvent choisir entre **paiement à la livraison** et **Orange Money / Wave** lors de la commande. Cependant, ces options ne sont pas encore connectées à un vrai système de paiement : le client sélectionne un mode, mais aucune transaction réelle n'est déclenchée ni vérifiée.

L'objectif  est de **connecter ces boutons à un vrai prestataire de paiement** pour que :
- Le client soit redirigé vers une page de paiement sécurisée
- Le paiement soit confirmé automatiquement avant de valider la commande
- La transformatrice reçoive une notification de paiement reçu

---

## Ce qu'il faut faire (côté technique)

### 1. Choisir un prestataire de paiement

Pour le Sénégal, trois options sont disponibles :

| Prestataire | Orange Money | Wave | Frais | Délai d'activation |
|-------------|:---:|:---:|-------|-------------------|
| **PayDunya** | ✅ | ✅ | ~2% par transaction | 5–10 jours ouvrés |
| **CinetPay** | ✅ | ✅ | ~2–3% | 5–10 jours ouvrés |
| **InTouch** | ✅ | ❌ | Variable | 7–15 jours |

**Recommandation : PayDunya** — le plus utilisé au Sénégal, documentation en français, SDK Python disponible, support Orange Money + Wave + carte bancaire.

---

### 2. Démarche d'activation (à faire )

Pour activer un compte PayDunya, il faut fournir à PayDunya :

1. **Registre de commerce (NINEA)** de l'entreprise ou de l'auto-entrepreneur
2. **Pièce d'identité** du gérant (CNI ou passeport)
3. **RIB bancaire** ou numéro de compte Orange Money Business
4. **Description de l'activité** (vente de riz en ligne)
5. **URL du site** : https://yeesnaa.com

S'inscrire sur : **https://paydunya.com/register**

Délai estimé : **5 à 10 jours ouvrés** après dépôt des documents.

---

### 3. Ce que PayDunya fournit après activation

- Une **clé API de test** (pour développer et tester sans vrai argent)
- Une **clé API de production** (pour les vraies transactions)
- Un **dashboard** pour voir toutes les transactions en temps réel
- Des **webhooks** : une URL que PayDunya appelle automatiquement quand un paiement est confirmé

---

### 4. Ce que le développeur fait une fois les clés reçues

| Étape | Description |
|-------|-------------|
| Intégrer le SDK PayDunya | Installer la librairie Python dans le projet |
| Créer la vue de paiement | Quand le client clique "Payer par Orange Money", une page sécurisée PayDunya s'ouvre |
| Configurer le webhook | PayDunya envoie une confirmation → la commande passe automatiquement en "Payée" |
| Sécuriser le total | Le montant est calculé côté serveur, jamais côté client |
| Ajouter les en-têtes HTTPS | Déjà en place sur yeesnaa.com (Let's Encrypt actif) |
| Tests complets | Simuler des paiements réussis, échoués, annulés |

---

## Ce qui ne change pas pour la cliente

- L'espace transformatrice reste identique
- Les commandes apparaissent toujours dans le tableau de bord
- Un nouveau statut **"Paiement en attente"** s'ajoutera pour distinguer les commandes payées en ligne de celles en paiement à la livraison
- Aucune donnée bancaire n'est jamais stockée sur le serveur Yeesnaa — tout est géré par PayDunya

---

## Ce qui ne change pas pour les clients

- Le tunnel de commande reste identique (panier → finaliser → confirmation)
- Après avoir cliqué "Payer par Orange Money", ils reçoivent une **notification push sur leur téléphone** pour valider le paiement
- Après validation, ils sont redirigés automatiquement vers la page de confirmation de commande

---

## Résumé des actions à mener

| Qui | Quoi | Quand |
|-----|------|-------|
| **Cliente** | S'inscrire sur PayDunya avec les documents de l'entreprise | Dès que possible |
| **Cliente** | Fournir les clés API au développeur | Après activation (5–10 jours) |
| **Développeur** | Intégrer PayDunya dans le code | Dès réception des clés |
| **Développeur** | Tests en environnement de staging | 1–2 jours après intégration |
| **Développeur** | Déploiement en production | Après validation des tests |

---

## Note importante

> Le paiement à la livraison (paiement en cash au moment de la réception) **reste disponible** en parallèle. L'intégration Mobile Money ajoute une option supplémentaire, elle ne remplace pas l'existant.

> Tant que les clés API PayDunya ne sont pas disponibles, le code actuel de Yeesnaa fonctionne parfaitement — les clients peuvent commander et payer à la livraison sans interruption.

---

*Document rédigé le 1er septembre 2026 — Projet Yeesnaa Connect*
