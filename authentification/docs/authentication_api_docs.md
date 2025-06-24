# Feuille de Route de l'API d'Authentification

Ce document sert de feuille de route pour le développement de l'API d'authentification. Il est divisé en deux parties : les fonctionnalités **actuellement implémentées** et les fonctionnalités **planifiées**.

> Pour une documentation technique détaillée des endpoints actuels, consultez le fichier [`api_docs_current.md`](./api_docs_current.md).

---

## Partie 1 : Fonctionnalités Implémentées (Core Auth)

Cette section couvre les fonctionnalités de base qui sont **déjà fonctionnelles**.

1.  **Inscription (`/api/auth/register/`)**
    - **Statut**: ✅ **Terminé**

2.  **Connexion (`/api/auth/login/`)**
    - **Statut**: ✅ **Terminé**

3.  **Rafraîchissement de Token (`/api/auth/refresh/`)**
    - **Statut**: ✅ **Terminé**

4.  **Informations Utilisateur (`/api/auth/me/`)**
    - **Statut**: ✅ **Terminé**

---

## Partie 2 : Fonctionnalités Planifiées

Cette section décrit les fonctionnalités qui seront développées dans les prochaines versions.

### Gestion du Profil Utilisateur

1.  **Mise à jour du profil (`PATCH /api/auth/me/`)**
    - **Description**: Permettre à l'utilisateur de mettre à jour ses propres informations.
    - **Statut**: ⏳ **À faire**

2.  **Changement de mot de passe (`POST /api/auth/change-password/`)**
    - **Description**: Permettre à un utilisateur connecté de changer son mot de passe.
    - **Statut**: ⏳ **À faire**

3.  **Déconnexion (`POST /api/auth/logout/`)**
    - **Description**: Invalider le token de rafraîchissement de l'utilisateur.
    - **Statut**: ⏳ **À faire**

### Fonctionnalités Avancées (Admin)

Pour le détail des fonctionnalités de gestion des utilisateurs, des rôles et des invitations par les administrateurs, consultez le document [**authentication_api_docs_advanced.md**](./authentication_api_docs_advanced.md). Il contient le plan de développement pour les fonctionnalités suivantes :

-   Gestion complète des utilisateurs (CRUD)
-   Gestion des rôles et permissions
-   Système d'invitations
-   **Statut**: ⏳ **À faire**