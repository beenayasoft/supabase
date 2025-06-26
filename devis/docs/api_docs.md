# API de Devis

Cette documentation détaille les endpoints disponibles pour la gestion des devis et des éléments de devis dans l'application.

## Structure des données

### Modèle de Devis (Quote)

Un devis contient les informations suivantes:

- `id`: Identifiant unique du devis (UUID)
- `number`: Numéro de devis (ex: DEV-2025-001)
- `status`: Statut du devis (draft, sent, accepted, rejected, expired, cancelled)
- `tier`: Relation avec le client (Tiers)
- `opportunity`: Relation avec l'opportunité associée (optionnel)
- `client_name`: Nom du client
- `client_address`: Adresse du client (optionnel)
- `project_name`: Nom du projet (optionnel)
- `project_address`: Adresse du projet (optionnel)
- `issue_date`: Date d'émission
- `expiry_date`: Date d'expiration (optionnel)
- `validity_period`: Durée de validité en jours (défaut: 30)
- `notes`: Notes additionnelles (optionnel)
- `terms_and_conditions`: Conditions générales (optionnel)
- `total_ht`: Montant total HT
- `total_vat`: Montant total de TVA
- `total_ttc`: Montant total TTC
- `created_at`: Date de création
- `updated_at`: Date de dernière mise à jour
- `created_by`: Créé par (optionnel)
- `updated_by`: Dernière mise à jour par (optionnel)

### Modèle d'Élément de Devis (QuoteItem)

Un élément de devis contient:

- `id`: Identifiant unique (UUID)
- `quote`: Relation avec le devis parent
- `type`: Type d'élément (product, service, work, chapter, section, discount)
- `parent`: Relation avec l'élément parent (pour les éléments hiérarchiques)
- `position`: Position dans le devis
- `reference`: Référence (optionnel)
- `designation`: Désignation
- `description`: Description détaillée (optionnel)
- `unit`: Unité (optionnel)
- `quantity`: Quantité
- `unit_price`: Prix unitaire
- `discount`: Remise en pourcentage (optionnel)
- `vat_rate`: Taux de TVA (0%, 5.5%, 10%, 20%)
- `margin`: Marge en pourcentage (optionnel)
- `total_ht`: Montant total HT
- `total_ttc`: Montant total TTC
- `work_id`: Identifiant de l'ouvrage (optionnel)
- `created_at`: Date de création
- `updated_at`: Date de dernière mise à jour

## Endpoints de Devis

### 1. Liste des devis

Récupère la liste des devis avec pagination et filtres.

- **URL**: `/api/quotes/`
- **Méthode**: `GET`
- **Auth requise**: Oui

**Paramètres de requête**:
```
page: integer (optionnel, défaut=1)
page_size: integer (optionnel, défaut=10, max=50)
search: string (optionnel, recherche textuelle)
status: string (optionnel, filtre par statut)
status_list: string (optionnel, filtres multiples par statut, séparés par virgule)
client_id: string (optionnel, filtre par client)
date_from: date (optionnel, filtre par date d'émission minimale)
date_to: date (optionnel, filtre par date d'émission maximale)
min_amount: number (optionnel, filtre par montant minimum)
max_amount: number (optionnel, filtre par montant maximum)
ordering: string (optionnel, tri par champ)
```

**Réponse de succès (200 OK)**:
```json
{
  "results": [
    {
      "id": "uuid",
      "number": "string",
      "status": "string",
      "client_name": "string",
      "project_name": "string",
      "issue_date": "date",
      "expiry_date": "date",
      "total_ht": "number",
      "total_vat": "number",
      "total_ttc": "number",
      "created_at": "datetime",
      "updated_at": "datetime"
    }
  ],
  "pagination": {
    "count": "integer",
    "num_pages": "integer",
    "current_page": "integer",
    "page_size": "integer",
    "has_next": "boolean",
    "has_previous": "boolean",
    "next_page": "integer",
    "previous_page": "integer"
  }
}
```

### 2. Détails d'un devis

Récupère les détails complets d'un devis.

- **URL**: `/api/quotes/{id}/`
- **Méthode**: `GET`
- **Auth requise**: Oui

**Réponse de succès (200 OK)**:
```json
{
  "id": "uuid",
  "number": "string",
  "status": "string",
  "tier": {
    "id": "uuid",
    "nom": "string"
  },
  "opportunity": {
    "id": "uuid",
    "name": "string"
  },
  "client_name": "string",
  "client_address": "string",
  "project_name": "string",
  "project_address": "string",
  "issue_date": "date",
  "expiry_date": "date",
  "validity_period": "integer",
  "notes": "string",
  "terms_and_conditions": "string",
  "items": [
    {
      "id": "uuid",
      "type": "string",
      "parent": "uuid",
      "position": "integer",
      "reference": "string",
      "designation": "string",
      "description": "string",
      "unit": "string",
      "quantity": "number",
      "unit_price": "number",
      "discount": "number",
      "vat_rate": "string",
      "margin": "number",
      "total_ht": "number",
      "total_ttc": "number",
      "work_id": "string",
      "children": [
        // Items enfants récursifs avec la même structure
      ]
    }
  ],
  "total_ht": "number",
  "total_vat": "number",
  "total_ttc": "number",
  "created_at": "datetime",
  "updated_at": "datetime",
  "created_by": "string",
  "updated_by": "string"
}
```

### 3. Créer un devis

Crée un nouveau devis.

- **URL**: `/api/quotes/`
- **Méthode**: `POST`
- **Auth requise**: Oui

**Corps de la requête**:
```json
{
  "tier": "uuid",
  "opportunity": "uuid (optionnel)",
  "client_name": "string",
  "client_address": "string (optionnel)",
  "project_name": "string (optionnel)",
  "project_address": "string (optionnel)",
  "issue_date": "date",
  "validity_period": "integer (optionnel)",
  "notes": "string (optionnel)",
  "terms_and_conditions": "string (optionnel)"
}
```

**Réponse de succès (201 CREATED)**:
```json
{
  "id": "uuid",
  "number": "string",
  "status": "draft",
  "tier": "uuid",
  "opportunity": "uuid",
  "client_name": "string",
  "client_address": "string",
  "project_name": "string",
  "project_address": "string",
  "issue_date": "date",
  "expiry_date": "date",
  "validity_period": "integer",
  "notes": "string",
  "terms_and_conditions": "string",
  "total_ht": "number",
  "total_vat": "number",
  "total_ttc": "number",
  "created_at": "datetime",
  "updated_at": "datetime",
  "created_by": "string"
}
```

### 4. Mettre à jour un devis

Met à jour un devis existant.

- **URL**: `/api/quotes/{id}/`
- **Méthode**: `PUT`
- **Auth requise**: Oui

**Corps de la requête**: Identique à la création de devis

**Réponse de succès (200 OK)**: Identique à la réponse de création de devis

### 5. Mettre à jour partiellement un devis

Met à jour partiellement un devis existant.

- **URL**: `/api/quotes/{id}/`
- **Méthode**: `PATCH`
- **Auth requise**: Oui

**Corps de la requête**: Champs à mettre à jour

**Réponse de succès (200 OK)**: Identique à la réponse de création de devis

### 6. Supprimer un devis

Supprime un devis existant.

- **URL**: `/api/quotes/{id}/`
- **Méthode**: `DELETE`
- **Auth requise**: Oui

**Réponse de succès (204 NO CONTENT)**

### 7. Statistiques des devis

Récupère des statistiques sur les devis.

- **URL**: `/api/quotes/stats/`
- **Méthode**: `GET`
- **Auth requise**: Oui

**Réponse de succès (200 OK)**:
```json
{
  "total_count": "integer",
  "draft_count": "integer",
  "sent_count": "integer",
  "accepted_count": "integer",
  "rejected_count": "integer",
  "expired_count": "integer",
  "cancelled_count": "integer",
  "total_amount": "number",
  "average_amount": "number",
  "conversion_rate": "number",
  "monthly_stats": [
    {
      "month": "string",
      "count": "integer",
      "amount": "number"
    }
  ]
}
```

### 8. Marquer un devis comme envoyé

Change le statut d'un devis de brouillon à envoyé.

- **URL**: `/api/quotes/{id}/mark_as_sent/`
- **Méthode**: `POST`
- **Auth requise**: Oui

**Corps de la requête**:
```json
{
  "send_date": "date (optionnel, défaut=aujourd'hui)"
}
```

**Réponse de succès (200 OK)**:
```json
{
  "id": "uuid",
  "number": "string",
  "status": "sent",
  "updated_at": "datetime"
}
```

### 9. Marquer un devis comme accepté

Change le statut d'un devis à accepté.

- **URL**: `/api/quotes/{id}/mark_as_accepted/`
- **Méthode**: `POST`
- **Auth requise**: Oui

**Corps de la requête**:
```json
{
  "acceptance_date": "date (optionnel, défaut=aujourd'hui)",
  "notes": "string (optionnel)"
}
```

**Réponse de succès (200 OK)**:
```json
{
  "id": "uuid",
  "number": "string",
  "status": "accepted",
  "updated_at": "datetime"
}
```

### 10. Marquer un devis comme refusé

Change le statut d'un devis à refusé.

- **URL**: `/api/quotes/{id}/mark_as_rejected/`
- **Méthode**: `POST`
- **Auth requise**: Oui

**Corps de la requête**:
```json
{
  "rejection_date": "date (optionnel, défaut=aujourd'hui)",
  "reason": "string (optionnel)"
}
```

**Réponse de succès (200 OK)**:
```json
{
  "id": "uuid",
  "number": "string",
  "status": "rejected",
  "updated_at": "datetime"
}
```

### 11. Marquer un devis comme annulé

Change le statut d'un devis à annulé.

- **URL**: `/api/quotes/{id}/mark_as_cancelled/`
- **Méthode**: `POST`
- **Auth requise**: Oui

**Corps de la requête**:
```json
{
  "cancellation_date": "date (optionnel, défaut=aujourd'hui)",
  "reason": "string (optionnel)"
}
```

**Réponse de succès (200 OK)**:
```json
{
  "id": "uuid",
  "number": "string",
  "status": "cancelled",
  "updated_at": "datetime"
}
```

### 12. Dupliquer un devis

Crée une copie d'un devis existant.

- **URL**: `/api/quotes/{id}/duplicate/`
- **Méthode**: `POST`
- **Auth requise**: Oui

**Corps de la requête**:
```json
{
  "new_client_id": "uuid (optionnel)",
  "new_project_name": "string (optionnel)",
  "include_items": "boolean (optionnel, défaut=true)",
  "reset_status": "boolean (optionnel, défaut=true)"
}
```

**Réponse de succès (201 CREATED)**:
```json
{
  "id": "uuid",
  "number": "string",
  "status": "draft",
  "original_quote_id": "uuid",
  "client_name": "string",
  "project_name": "string",
  "issue_date": "date",
  "total_ht": "number",
  "total_vat": "number",
  "total_ttc": "number"
}
```

### 13. Exporter un devis

Exporte un devis dans différents formats.

- **URL**: `/api/quotes/{id}/export/`
- **Méthode**: `POST`
- **Auth requise**: Oui

**Corps de la requête**:
```json
{
  "format": "string (pdf, excel, csv)",
  "include_details": "boolean (optionnel, défaut=true)",
  "template": "string (optionnel)"
}
```

**Réponse de succès (200 OK)**:
```json
{
  "file_url": "string",
  "file_name": "string",
  "file_type": "string",
  "file_size": "integer"
}
```

### 14. Mise à jour en lot d'un devis

Met à jour un devis complet avec tous ses éléments en une seule opération.

- **URL**: `/api/quotes/{id}/bulk_update/`
- **Méthode**: `PUT`
- **Auth requise**: Oui

**Corps de la requête**:
```json
{
  "quote": {
    // Données du devis à mettre à jour
  },
  "items": [
    {
      "id": "uuid (si existant)",
      "action": "create|update|delete",
      // Données de l'élément
    }
  ]
}
```

**Réponse de succès (200 OK)**:
```json
{
  "quote": {
    // Devis mis à jour
  },
  "items": [
    // Éléments mis à jour
  ],
  "stats": {
    "created": "integer",
    "updated": "integer",
    "deleted": "integer"
  }
}
```

### 15. Création en lot d'un devis

Crée un devis complet avec tous ses éléments en une seule opération.

- **URL**: `/api/quotes/bulk_create/`
- **Méthode**: `POST`
- **Auth requise**: Oui

**Corps de la requête**:
```json
{
  "quote": {
    // Données du devis à créer
  },
  "items": [
    {
      // Données des éléments à créer
    }
  ]
}
```

**Réponse de succès (201 CREATED)**:
```json
{
  "quote": {
    // Devis créé
  },
  "items": [
    // Éléments créés
  ]
}
```

## Endpoints d'Éléments de Devis

### 1. Liste des éléments de devis

Récupère la liste des éléments de devis.

- **URL**: `/api/quote-items/`
- **Méthode**: `GET`
- **Auth requise**: Oui

**Paramètres de requête**:
```
quote: uuid (optionnel, filtre par devis)
type: string (optionnel, filtre par type)
parent: uuid (optionnel, filtre par parent)
search: string (optionnel, recherche textuelle)
ordering: string (optionnel, tri par champ)
```

**Réponse de succès (200 OK)**:
```json
[
  {
    "id": "uuid",
    "quote": "uuid",
    "type": "string",
    "parent": "uuid",
    "position": "integer",
    "designation": "string",
    "reference": "string",
    "quantity": "number",
    "unit_price": "number",
    "total_ht": "number",
    "total_ttc": "number"
  }
]
```

### 2. Détails d'un élément de devis

Récupère les détails d'un élément de devis.

- **URL**: `/api/quote-items/{id}/`
- **Méthode**: `GET`
- **Auth requise**: Oui

**Réponse de succès (200 OK)**:
```json
{
  "id": "uuid",
  "quote": "uuid",
  "type": "string",
  "parent": "uuid",
  "position": "integer",
  "reference": "string",
  "designation": "string",
  "description": "string",
  "unit": "string",
  "quantity": "number",
  "unit_price": "number",
  "discount": "number",
  "vat_rate": "string",
  "margin": "number",
  "total_ht": "number",
  "total_ttc": "number",
  "work_id": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### 3. Créer un élément de devis

Crée un nouvel élément de devis.

- **URL**: `/api/quote-items/`
- **Méthode**: `POST`
- **Auth requise**: Oui

**Corps de la requête**:
```json
{
  "quote": "uuid",
  "type": "string",
  "parent": "uuid (optionnel)",
  "position": "integer (optionnel)",
  "reference": "string (optionnel)",
  "designation": "string",
  "description": "string (optionnel)",
  "unit": "string (optionnel)",
  "quantity": "number",
  "unit_price": "number",
  "discount": "number (optionnel)",
  "vat_rate": "string",
  "margin": "number (optionnel)",
  "work_id": "string (optionnel)"
}
```

**Réponse de succès (201 CREATED)**:
```json
{
  "id": "uuid",
  "quote": "uuid",
  "type": "string",
  "parent": "uuid",
  "position": "integer",
  "reference": "string",
  "designation": "string",
  "description": "string",
  "unit": "string",
  "quantity": "number",
  "unit_price": "number",
  "discount": "number",
  "vat_rate": "string",
  "margin": "number",
  "total_ht": "number",
  "total_ttc": "number",
  "work_id": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### 4. Mettre à jour un élément de devis

Met à jour un élément de devis existant.

- **URL**: `/api/quote-items/{id}/`
- **Méthode**: `PUT`
- **Auth requise**: Oui

**Corps de la requête**: Identique à la création d'élément de devis

**Réponse de succès (200 OK)**: Identique à la réponse de création d'élément de devis

### 5. Mettre à jour partiellement un élément de devis

Met à jour partiellement un élément de devis existant.

- **URL**: `/api/quote-items/{id}/`
- **Méthode**: `PATCH`
- **Auth requise**: Oui

**Corps de la requête**: Champs à mettre à jour

**Réponse de succès (200 OK)**: Identique à la réponse de création d'élément de devis

### 6. Supprimer un élément de devis

Supprime un élément de devis existant.

- **URL**: `/api/quote-items/{id}/`
- **Méthode**: `DELETE`
- **Auth requise**: Oui

**Réponse de succès (204 NO CONTENT)**

### 7. Éléments d'un devis spécifique

Récupère tous les éléments d'un devis spécifique avec leur hiérarchie.

- **URL**: `/api/quote-items/by_quote/`
- **Méthode**: `GET`
- **Auth requise**: Oui

**Paramètres de requête**:
```
quote_id: uuid (requis)
```

**Réponse de succès (200 OK)**:
```json
[
  {
    "id": "uuid",
    "type": "string",
    "position": "integer",
    "reference": "string",
    "designation": "string",
    "description": "string",
    "unit": "string",
    "quantity": "number",
    "unit_price": "number",
    "discount": "number",
    "vat_rate": "string",
    "total_ht": "number",
    "total_ttc": "number",
    "children": [
      // Éléments enfants récursifs avec la même structure
    ]
  }
]
```

### 8. Réorganiser les éléments de devis

Réorganise l'ordre des éléments d'un devis.

- **URL**: `/api/quote-items/reorder/`
- **Méthode**: `POST`
- **Auth requise**: Oui

**Corps de la requête**:
```json
{
  "items": [
    {
      "id": "uuid",
      "position": "integer",
      "parent": "uuid (optionnel)"
    }
  ]
}
```

**Réponse de succès (200 OK)**:
```json
{
  "success": true,
  "message": "Éléments réorganisés avec succès",
  "updated_count": "integer"
}
```

### 9. Opérations en lot sur les éléments

Effectue des opérations en lot sur plusieurs éléments de devis.

- **URL**: `/api/quote-items/batch_operations/`
- **Méthode**: `POST`
- **Auth requise**: Oui

**Corps de la requête**:
```json
{
  "operations": [
    {
      "operation": "create|update|delete",
      "id": "uuid (pour update/delete)",
      "data": {
        // Données de l'élément pour create/update
      }
    }
  ]
}
```

**Réponse de succès (200 OK)**:
```json
{
  "success": true,
  "results": {
    "created": [
      // Éléments créés
    ],
    "updated": [
      // Éléments mis à jour
    ],
    "deleted": [
      // IDs des éléments supprimés
    ]
  }
}
```

## Codes d'erreur communs

- `400 Bad Request`: Requête invalide (données manquantes ou incorrectes)
- `401 Unauthorized`: Authentification requise
- `403 Forbidden`: Permissions insuffisantes
- `404 Not Found`: Ressource non trouvée
- `409 Conflict`: Conflit (par exemple, tentative de modification d'un devis déjà accepté)
- `500 Internal Server Error`: Erreur serveur 