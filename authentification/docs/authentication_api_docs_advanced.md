# Blueprint de l'API : Fonctionnalités Avancées

Ce document est le blueprint technique pour les fonctionnalités **planifiées** de l'API. Il sert de guide pour le développement futur.

> **Statut Général**: ⏳ **À faire**

---

## Module 1 : Gestion des Utilisateurs (Admin)

Endpoints permettant aux administrateurs de gérer l'ensemble des utilisateurs.

- **URL de base**: `/api/users/`
- **Permissions requises**: `IsAdminUser`

### 1.1. Lister et Filtrer les Utilisateurs
- **Endpoint**: `GET /api/users/`
- **Paramètres de requête**:
  - `search`: Recherche par nom, email, entreprise.
  - `status`: Filtre par statut (`active`, `inactive`, `pending`).
  - `role`: Filtre par ID de rôle.
  - `page`, `size`: Pagination.
- **Réponse**: Liste paginée d'utilisateurs.

### 1.2. Récupérer un Utilisateur Spécifique
- **Endpoint**: `GET /api/users/{id}/`
- **Réponse**: Détails complets de l'utilisateur, incluant ses rôles.

### 1.3. Mettre à Jour un Utilisateur
- **Endpoint**: `PATCH /api/users/{id}/`
- **Corps de la requête**: `{ "first_name": "...", "last_name": "...", "company": "..." }`
- **Réponse**: Utilisateur mis à jour.

### 1.4. Activer / Désactiver un Utilisateur
- **Endpoint (Activer)**: `POST /api/users/{id}/activate/`
- **Endpoint (Désactiver)**: `POST /api/users/{id}/deactivate/`
- **Réponse**: Message de confirmation.

### 1.5. Gérer les Rôles d'un Utilisateur
- **Endpoint**: `POST /api/users/{id}/update_roles/`
- **Corps de la requête**: `{ "roles": [1, 2, ...] }` (IDs des rôles)
- **Réponse**: Message de confirmation.

---

## Module 2 : Gestion des Invitations

Système permettant aux administrateurs d'inviter de nouveaux utilisateurs.

- **URL de base**: `/api/invitations/`

### 2.1. Créer et Envoyer une Invitation (Admin)
- **Endpoint**: `POST /api/invitations/`
- **Permissions**: `IsAdminUser`
- **Corps de la requête**: `{ "email": "...", "first_name": "...", "last_name": "...", "company": "...", "roles": [...] }`
- **Réponse**: Détails de l'invitation créée.

### 2.2. Lister les Invitations (Admin)
- **Endpoint**: `GET /api/invitations/`
- **Permissions**: `IsAdminUser`
- **Paramètres**: `is_accepted` (bool), pagination.
- **Réponse**: Liste des invitations.

### 2.3. Renvoyer une Invitation (Admin)
- **Endpoint**: `POST /api/invitations/{id}/resend/`
- **Permissions**: `IsAdminUser`
- **Réponse**: Message de confirmation.

### 2.4. Supprimer une Invitation (Admin)
- **Endpoint**: `DELETE /api/invitations/{id}/`
- **Permissions**: `IsAdminUser`
- **Réponse**: `204 NO CONTENT`.

### 2.5. Valider un Token d'Invitation (Public)
- **Endpoint**: `GET /api/invitations/{token}/validate/`
- **Permissions**: `AllowAny`
- **Réponse**: `{ "email", "first_name", ... }` si valide, sinon `404` ou `400`.

### 2.6. Accepter une Invitation (Public)
- **Endpoint**: `POST /api/invitations/{token}/accept/`
- **Permissions**: `AllowAny`
- **Corps de la requête**: `{ "password": "..." }`
- **Réponse**: Crée le compte utilisateur et retourne les tokens JWT.

---

## Module 3 : Gestion des Rôles (Admin)

- **URL de base**: `/api/roles/`
- **Permissions requises**: `IsAdminUser`

### 3.1. Lister les Rôles
- **Endpoint**: `GET /api/roles/`
- **Réponse**: Liste de tous les rôles disponibles dans le système.

### 3.2. Créer un Rôle
- **Endpoint**: `POST /api/roles/`
- **Corps de la requête**: `{ "name": "...", "description": "..." }`
- **Réponse**: Le nouveau rôle créé.

### 3.3. Mettre à Jour un Rôle
- **Endpoint**: `PATCH /api/roles/{id}/`
- **Réponse**: Le rôle mis à jour.

### 3.4. Supprimer un Rôle
- **Endpoint**: `DELETE /api/roles/{id}/`
- **Réponse**: `204 NO CONTENT`.

---

## Module 4 : Suivi et Statistiques

### 4.1. Suivi des Activités des Utilisateurs
- **Endpoint**: `GET /api/activities/`
- **Permissions**: `IsAdminUser`
- **Paramètres**: `user_id`, `action_type`, date range, pagination.
- **Réponse**: Liste des activités enregistrées.

### 4.2. Statistiques de Connexion
- **Endpoint**: `GET /api/statistics/logins/`
- **Permissions**: `IsAdminUser`
- **Réponse**: Résumé des statistiques de connexion.

---

## Module 5 : Documentation de l'API (Auto-générée)

### 5.1. Schéma OpenAPI
- **Endpoint**: `GET /api/schema/`
- **Permissions**: `AllowAny`
- **Réponse**: Schéma OpenAPI au format JSON.

### 5.2. Interface Swagger UI
- **Endpoint**: `GET /api/docs/`
- **Permissions**: `AllowAny`
- **Réponse**: Interface Swagger UI pour explorer l'API.