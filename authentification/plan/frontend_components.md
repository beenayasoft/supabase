# Composants Frontend - Module 1: Gestion des Utilisateurs et des Rôles

Ce document décrit les composants frontend à développer ou améliorer pour le module de gestion des utilisateurs et des rôles.

## 1. Page d'Administration

### Composant principal: `Administration.tsx`
- **Modifications nécessaires**:
  - Implémenter correctement la vérification des droits d'accès (actuellement désactivée)
  - Améliorer la structure de la page pour faciliter la navigation entre les onglets
  - Ajouter des indicateurs de chargement pendant les requêtes API

## 2. Gestion des Utilisateurs

### `UserManagement.tsx` (existant - à améliorer)
- **Fonctionnalités à ajouter**:
  - Recherche par nom/email
  - Filtrage par statut et rôle
  - Pagination
  - Confirmation pour les actions critiques (désactivation d'utilisateur)
  - Amélioration de l'affichage des rôles (badges avec couleurs distinctives)
  - Actions contextuelles selon le statut de l'utilisateur

### `UserDetailModal.tsx` (existant - à améliorer)
- **Fonctionnalités à ajouter**:
  - Vue par onglets (Informations, Rôles, Activité, Connexions)
  - Interface de modification des rôles
  - Historique des activités de l'utilisateur
  - Affichage des tokens de connexion actifs

### `UserStatusBadge.tsx` (existant - à améliorer)
- **Modifications nécessaires**:
  - Ajouter des couleurs distinctives pour chaque statut
  - Ajouter des tooltips explicatifs

### `RoleBadges.tsx` (existant - à améliorer)
- **Modifications nécessaires**:
  - Utiliser des couleurs spécifiques pour chaque rôle
  - Améliorer l'affichage pour plusieurs rôles
  - Ajouter des tooltips avec la description du rôle

## 3. Gestion des Invitations

### `InvitationManagement.tsx` (existant - à améliorer)
- **Fonctionnalités à ajouter**:
  - Filtrage par statut (acceptée/en attente)
  - Recherche par nom/email
  - Pagination
  - Affichage de la date d'expiration
  - Bouton pour renvoyer une invitation

### `InviteUserModal.tsx` (existant - à améliorer)
- **Modifications nécessaires**:
  - Amélioration de la validation des emails
  - Meilleure UX pour la sélection des rôles
  - Ajout d'un champ pour la durée de validité de l'invitation (optionnel)

## 4. Nouvelle Page d'Acceptation d'Invitation

### `AcceptInvitation.tsx` (à créer)
- **Fonctionnalités**:
  - Affichage des informations de l'invitation (nom, email, entreprise)
  - Formulaire de création de mot de passe
  - Validation des règles de complexité du mot de passe
  - Indicateur de force du mot de passe
  - Gestion des erreurs (invitation expirée, déjà acceptée, etc.)

## 5. Améliorations de l'API Client

### `auth.ts` (à améliorer)
- **Fonctions à ajouter**:
  - `validateInvitation`: Valider un token d'invitation
  - `acceptInvitation`: Accepter une invitation et créer un compte

### `admin.ts` (à améliorer)
- **Fonctions à ajouter ou compléter**:
  - Pagination et filtrage pour les requêtes de liste
  - Gestion des erreurs spécifiques
  - Types TypeScript pour toutes les requêtes et réponses

## 6. Hooks React

### `useAuth.tsx` (existant - à améliorer)
- **Fonctionnalités à ajouter**:
  - Vérification des rôles plus robuste
  - Gestion du token refresh
  - Stockage sécurisé des tokens d'authentification

### `useAdmin.tsx` (existant - à améliorer)
- **Fonctionnalités à ajouter**:
  - Fonctions pour les nouvelles opérations d'API
  - Pagination et filtrage côté client
  - Gestion d'état optimisée pour éviter les re-rendus inutiles

## 7. Composants UI génériques à améliorer

### Pagination (à créer)
- Composant réutilisable pour toutes les listes paginées

### Filtres de recherche (à créer)
- Composant réutilisable pour les filtres de recherche et de tri

### Confirmation Dialog (à créer)
- Modal de confirmation pour les actions critiques

## Maquettes et Wireframes

### Écran 1: Liste des Utilisateurs
```
+------------------------------------------------------+
| Utilisateurs & Accès              [+ Inviter]        |
| [Recherche...]                                       |
|                                                      |
| +--------------------------------------------------+ |
| | Nom        | Email      | Rôles        | Statut  | |
| |------------+------------+--------------+---------|
| | Jean Dupont| jean@ex.fr | [Admin][Gér] | ● Actif | |
| | Marie Martin| marie@e.fr| [Admin]      | ● Actif | |
| | Paul Simon | paul@ex.fr | [Adm][Opér]  | ○ Inactif|
| +--------------------------------------------------+ |
|                                                      |
| [◀] Pages: 1 2 3 ... [▶]                            |
+------------------------------------------------------+
```

### Écran 2: Modal d'Invitation
```
+----------------------------------------+
| Inviter un nouvel utilisateur       X  |
|                                        |
| Envoyez une invitation par email pour  |
| ajouter un nouvel utilisateur.         |
|                                        |
| +-------------+  +---------------+     |
| | Prénom      |  | Nom           |     |
| +-------------+  +---------------+     |
|                                        |
| +----------------------------------+   |
| | Email                            |   |
| +----------------------------------+   |
|                                        |
| +----------------------------------+   |
| | Entreprise                       |   |
| +----------------------------------+   |
|                                        |
| Rôles                                  |
| +----------------------------------+   |
| | Sélectionner un rôle         [▼] |   |
| +----------------------------------+   |
|                                        |
| [Administrateur][x] [Gérant][x]        |
|                                        |
| [     Annuler    ] [Envoyer l'invitation]|
+----------------------------------------+
```

### Écran 3: Page d'Acceptation d'Invitation
```
+----------------------------------------+
| Créer votre compte                     |
|                                        |
| Vous avez été invité à rejoindre       |
| Entreprise XYZ                         |
|                                        |
| Nom:           Jean Dupont             |
| Email:         jean.dupont@example.com |
| Entreprise:    Entreprise XYZ          |
|                                        |
| +----------------------------------+   |
| | Mot de passe                     |   |
| +----------------------------------+   |
|                                        |
| +----------------------------------+   |
| | Confirmer le mot de passe        |   |
| +----------------------------------+   |
|                                        |
| [      Créer mon compte      ]         |
+----------------------------------------+
```

## Responsivité

Tous les composants doivent être conçus pour fonctionner correctement sur:
- Écrans larges (desktop)
- Tablettes
- Smartphones

## Thèmes et Accessibilité

- Supporter les thèmes clair et sombre
- Assurer l'accessibilité (contraste, navigation au clavier, etc.)
- Utiliser les composants UI existants (shadcn/ui) pour maintenir la cohérence 