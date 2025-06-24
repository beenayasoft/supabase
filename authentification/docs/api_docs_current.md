# API d'Authentification

Cette documentation détaille les endpoints actuellement implémentés pour l'authentification et la gestion des profils utilisateurs de base.

> **Note**: Les fonctionnalités avancées (gestion des utilisateurs par les administrateurs, invitations, rôles, etc.) sont décrites dans le plan de développement mais ne sont pas encore implémentées.

## Endpoints d'Authentification

### 1. Inscription d'un nouvel utilisateur

Crée un nouveau compte utilisateur et retourne les tokens d'authentification.

- **URL**: `/api/auth/register/`
- **Méthode**: `POST`
- **Auth requise**: Non

**Corps de la requête**:
```json
{
  "email": "user@example.com",
  "username": "string",
  "password": "string",
  "password2": "string",
  "first_name": "string",
  "last_name": "string",
  "company": "string"
}
```

**Réponse de succès (201 CREATED)**:
```json
{
  "user": {
    "id": "integer",
    "email": "string",
    "username": "string",
    "first_name": "string",
    "last_name": "string",
    "company": "string"
  },
  "refresh": "string",
  "access": "string"
}
```

### 2. Connexion (Obtenir un token JWT)

Authentifie un utilisateur avec son email et mot de passe, et retourne une paire de tokens JWT.

- **URL**: `/api/auth/login/`
- **Méthode**: `POST`
- **Auth requise**: Non

**Corps de la requête**:
```json
{
  "email": "user@example.com",
  "password": "string"
}
```

**Réponse de succès (200 OK)**:
```json
{
  "refresh": "string",
  "access": "string"
}
```
> **Note**: Pour que la connexion par email fonctionne, le modèle utilisateur de Django doit être configuré avec `USERNAME_FIELD = 'email'`. Par défaut, Django utilise `username`.

### 3. Rafraîchir le token d'accès

Permet d'obtenir un nouveau token d'accès en utilisant un token de rafraîchissement valide.

- **URL**: `/api/auth/refresh/`
- **Méthode**: `POST`
- **Auth requise**: Non

**Corps de la requête**:
```json
{
  "refresh": "string"
}
```

**Réponse de succès (200 OK)**:
```json
{
  "access": "string"
}
```

### 4. Récupérer les informations de l'utilisateur connecté

Retourne les informations du profil de l'utilisateur actuellement authentifié.

- **URL**: `/api/auth/me/`
- **Méthode**: `GET`
- **Auth requise**: Oui (Token d'accès valide requis dans l'en-tête `Authorization`)

**Réponse de succès (200 OK)**:
```json
{
  "id": "integer",
  "email": "string",
  "username": "string",
  "first_name": "string",
  "last_name": "string",
  "company": "string"
}
```
