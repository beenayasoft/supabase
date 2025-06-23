# API Routes - Module 1: Gestion des Utilisateurs et des Rôles

Ce document liste les endpoints à développer ou améliorer pour supporter la gestion des utilisateurs et des rôles.

## 1. Gestion des Utilisateurs

### Listing et filtrage des utilisateurs
- **URL**: `/auth/users/`
- **Méthode**: `GET`
- **Auth requise**: Oui (Administrateur uniquement)
- **Paramètres**:
  - `search`: Recherche par nom, prénom ou email
  - `status`: Filtrer par statut (active, inactive, pending)
  - `role`: Filtrer par ID de rôle
  - `page`, `size`: Pagination
- **Réponse de succès**:
  - **Code**: 200 OK
  - **Contenu**: Liste d'utilisateurs avec pagination

### Récupérer un utilisateur spécifique
- **URL**: `/auth/users/{id}/`
- **Méthode**: `GET`
- **Auth requise**: Oui (Administrateur uniquement)
- **Réponse de succès**:
  - **Code**: 200 OK
  - **Contenu**: Détails de l'utilisateur (avec rôles)

### Mettre à jour un utilisateur
- **URL**: `/auth/users/{id}/`
- **Méthode**: `PATCH`
- **Auth requise**: Oui (Administrateur uniquement)
- **Corps de la requête**:
```json
{
  "first_name": "string",
  "last_name": "string",
  "company": "string"
}
```
- **Réponse de succès**:
  - **Code**: 200 OK
  - **Contenu**: Utilisateur mis à jour

### Activer un utilisateur
- **URL**: `/auth/users/{id}/activate/`
- **Méthode**: `POST`
- **Auth requise**: Oui (Administrateur uniquement)
- **Réponse de succès**:
  - **Code**: 200 OK
  - **Contenu**: 
```json
{
  "detail": "Utilisateur activé avec succès."
}
```

### Désactiver un utilisateur
- **URL**: `/auth/users/{id}/deactivate/`
- **Méthode**: `POST`
- **Auth requise**: Oui (Administrateur uniquement)
- **Réponse de succès**:
  - **Code**: 200 OK
  - **Contenu**: 
```json
{
  "detail": "Utilisateur désactivé avec succès."
}
```

### Mettre à jour les rôles d'un utilisateur
- **URL**: `/auth/users/{id}/update_roles/`
- **Méthode**: `POST`
- **Auth requise**: Oui (Administrateur uniquement)
- **Corps de la requête**:
```json
{
  "roles": [1, 2]  // IDs des rôles
}
```
- **Réponse de succès**:
  - **Code**: 200 OK
  - **Contenu**: 
```json
{
  "detail": "Rôles mis à jour avec succès."
}
```

## 2. Gestion des Invitations

### Créer une invitation
- **URL**: `/auth/invitations/`
- **Méthode**: `POST`
- **Auth requise**: Oui (Administrateur uniquement)
- **Corps de la requête**:
```json
{
  "email": "string",
  "first_name": "string",
  "last_name": "string",
  "company": "string",
  "roles": [1, 2]  // IDs des rôles
}
```
- **Réponse de succès**:
  - **Code**: 201 CREATED
  - **Contenu**: Détails de l'invitation créée

### Lister les invitations
- **URL**: `/auth/invitations/`
- **Méthode**: `GET`
- **Auth requise**: Oui (Administrateur uniquement)
- **Paramètres**:
  - `search`: Recherche par nom, prénom ou email
  - `is_accepted`: Filtrer par statut d'acceptation
  - `page`, `size`: Pagination
- **Réponse de succès**:
  - **Code**: 200 OK
  - **Contenu**: Liste des invitations

### Renvoyer une invitation
- **URL**: `/auth/invitations/{id}/resend/`
- **Méthode**: `POST`
- **Auth requise**: Oui (Administrateur uniquement)
- **Réponse de succès**:
  - **Code**: 200 OK
  - **Contenu**: 
```json
{
  "detail": "Invitation renvoyée avec succès."
}
```

### Supprimer une invitation
- **URL**: `/auth/invitations/{id}/`
- **Méthode**: `DELETE`
- **Auth requise**: Oui (Administrateur uniquement)
- **Réponse de succès**:
  - **Code**: 204 NO CONTENT

### Valider un token d'invitation
- **URL**: `/auth/invitations/{token}/validate/`
- **Méthode**: `GET`
- **Auth requise**: Non
- **Réponse de succès**:
  - **Code**: 200 OK
  - **Contenu**:
```json
{
  "email": "string",
  "first_name": "string",
  "last_name": "string",
  "company": "string"
}
```
- **Réponse d'erreur**:
  - **Code**: 400 BAD REQUEST (expirée) ou 404 NOT FOUND (invalide)
  - **Contenu**:
```json
{
  "detail": "Cette invitation a expiré." 
}
```

### Accepter une invitation
- **URL**: `/auth/invitations/{token}/accept/`
- **Méthode**: `POST`
- **Auth requise**: Non
- **Corps de la requête**:
```json
{
  "password": "string"
}
```
- **Réponse de succès**:
  - **Code**: 200 OK
  - **Contenu**: 
```json
{
  "detail": "Compte créé avec succès",
  "refresh": "string",
  "access": "string"
}
```

## 3. Gestion des Rôles

### Lister les rôles
- **URL**: `/auth/roles/`
- **Méthode**: `GET`
- **Auth requise**: Oui (Administrateur uniquement)
- **Réponse de succès**:
  - **Code**: 200 OK
  - **Contenu**: Liste des rôles disponibles
```json
[
  {
    "id": 1,
    "name": "Administrateur",
    "description": "Accès total..."
  },
  // ...
]
```

## Notes techniques

1. Tous les endpoints doivent être sécurisés avec les permissions appropriées
2. Les validations suivantes doivent être implémentées:
   - Email unique pour les utilisateurs et les invitations
   - Vérification de la validité et de l'expiration des tokens d'invitation
   - Politique de mots de passe (min 8 caractères, majuscule, minuscule, chiffre)
3. Les invitations doivent expirer après 72 heures
4. Toutes les actions sensibles doivent être journalisées 