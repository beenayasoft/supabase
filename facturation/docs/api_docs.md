# API de Facturation

Cette documentation détaille les endpoints disponibles pour la gestion des factures et des paiements, basés sur les user stories 5.1 à 5.5.

> **Note**: Cette API s'intègre parfaitement avec le frontend existant et évite tout conflit avec l'API devis (`/api/quotes/`).

## Architecture et Relations

### 🔗 Intégration avec les modules existants

**Relations avec le module Tiers** :
- Relation ForeignKey directe : `Invoice.tier → Tiers`
- Auto-remplissage automatique des informations client (`client_name`, `client_address`)
- Récupération de l'adresse de facturation principale depuis `tier.adresses`

**Relations avec le module Devis** :
- Relation ForeignKey optionnelle : `Invoice.quote → Quote`
- Synchronisation automatique des données projet (`project_name`, `project_address`)
- Numérotation cohérente (`quote_number` automatiquement rempli)

**Gestion des projets/chantiers** :
- En attente du module chantier : stockage temporaire via chaînes de caractères
- `project_name`, `project_address`, `project_reference` prêts pour migration future
- Récupération automatique depuis le devis lié si disponible

### 🎯 Compatibilité Frontend

**Propriétés calculées** : Toutes les propriétés attendues par le frontend sont exposées via des propriétés calculées :
- `client_id` → `str(invoice.tier.id)`
- `project_id` → `invoice.project_reference`
- `quote_id` → `str(invoice.quote.id)`
- `credit_note_id` → `str(invoice.credit_note.id)`
- `original_invoice_id` → `str(invoice.original_invoice.id)`

**Hiérarchie des éléments** : Support complet de la hiérarchie parent/enfant comme dans `QuoteItem`
- `parent_id` exposé comme propriété calculée depuis `parent.id`
- Support des chapitres, sections et sous-éléments

### 🚀 Fonctionnalités avancées

**Auto-remplissage intelligent** :
1. Informations client depuis `Tiers`
2. Informations projet depuis `Quote` (si lié)
3. Calculs automatiques des totaux et montants

**Numérotation automatique** :
- Format : `FAC-YYYY-XXX` (ex: FAC-2025-001)
- Génération lors de la validation (passage de "Brouillon" à "Émise")
- Séquence par année calendaire

## Structure des données

### Modèle de Facture (Invoice)

Basé sur l'interface frontend `Invoice`, une facture contient :

- `id`: Identifiant unique (string)
- `number`: Numéro de facture (ex: "FAC-2025-001" ou "Brouillon")
- `status`: Statut ('draft' | 'sent' | 'overdue' | 'partially_paid' | 'paid' | 'cancelled' | 'cancelled_by_credit_note')
- `clientId`: Identifiant du client (string)
- `clientName`: Nom du client (string)
- `clientAddress`: Adresse du client (optionnel)
- `projectId`: Identifiant du projet (optionnel)
- `projectName`: Nom du projet (optionnel)
- `projectAddress`: Adresse du projet (optionnel)
- `issueDate`: Date d'émission (format ISO date string)
- `dueDate`: Date d'échéance (format ISO date string)
- `paymentTerms`: Délai de paiement en jours (optionnel)
- `items`: Liste des éléments de facture (InvoiceItem[])
- `notes`: Notes additionnelles (optionnel)
- `termsAndConditions`: Conditions générales (optionnel)
- `totalHT`: Montant total HT (number)
- `totalVAT`: Montant total TVA (number)
- `totalTTC`: Montant total TTC (number)
- `paidAmount`: Montant déjà payé (number)
- `remainingAmount`: Montant restant à payer (number)
- `payments`: Liste des paiements (Payment[])
- `quoteId`: ID du devis d'origine (optionnel)
- `quoteNumber`: Numéro du devis d'origine (optionnel)
- `creditNoteId`: ID de l'avoir (optionnel)
- `originalInvoiceId`: ID de la facture d'origine si avoir (optionnel)
- `createdAt`: Date de création (ISO datetime string)
- `updatedAt`: Date de mise à jour (ISO datetime string)
- `createdBy`: Créé par (optionnel)
- `updatedBy`: Mis à jour par (optionnel)

### Modèle d'Élément de Facture (InvoiceItem)

Basé sur l'interface frontend `InvoiceItem` :

- `id`: Identifiant unique (string)
- `type`: Type d'élément ('product' | 'service' | 'work' | 'chapter' | 'section' | 'discount' | 'advance_payment')
- `parentId`: ID de l'élément parent (optionnel)
- `position`: Position dans la facture (number)
- `reference`: Référence (optionnel)
- `designation`: Désignation (string)
- `description`: Description détaillée (optionnel)
- `unit`: Unité (optionnel)
- `quantity`: Quantité (number)
- `unitPrice`: Prix unitaire (number)
- `discount`: Remise en pourcentage (optionnel)
- `vatRate`: Taux de TVA (0 | 7 | 10 | 14 | 20)
- `totalHT`: Montant total HT (number)
- `totalTTC`: Montant total TTC (number)
- `workId`: Identifiant de l'ouvrage (optionnel)

### Modèle de Paiement (Payment)

Basé sur l'interface frontend `Payment` :

- `id`: Identifiant unique (string)
- `date`: Date du paiement (ISO date string)
- `amount`: Montant du paiement (number)
- `method`: Méthode de paiement ('bank_transfer' | 'check' | 'cash' | 'card' | 'other')
- `reference`: Référence du paiement (optionnel)
- `notes`: Notes additionnelles (optionnel)

## Endpoints de Facturation

### 1. Liste des factures

Récupère la liste des factures avec pagination et filtres.

- **URL**: `/api/invoices/`
- **Méthode**: `GET`
- **Auth requise**: Oui

**Paramètres de requête**:
```
page: integer (optionnel, défaut=1)
page_size: integer (optionnel, défaut=20)
search: string (optionnel, recherche textuelle)
status: string (optionnel, filtre par statut)
clientId: string (optionnel, filtre par client)
dateFrom: string (optionnel, date ISO)
dateTo: string (optionnel, date ISO)
minAmount: number (optionnel, montant minimum)
maxAmount: number (optionnel, montant maximum)
ordering: string (optionnel, tri par champ)
```

**Réponse de succès (200 OK)**:
```json
{
  "count": 45,
  "next": "http://api/invoices/?page=2",
  "previous": null,
  "results": [
    {
      "id": "1",
      "number": "FAC-2025-001",
      "status": "sent",
      "clientId": "1",
      "clientName": "Dupont Construction",
      "projectName": "Villa Moderne",
      "issueDate": "2025-01-15",
      "dueDate": "2025-02-15",
      "totalHT": 3500,
      "totalVAT": 700,
      "totalTTC": 4200,
      "paidAmount": 0,
      "remainingAmount": 4200,
      "createdAt": "2025-01-15T10:00:00Z",
      "updatedAt": "2025-01-15T10:00:00Z"
    }
  ]
}
```

### 2. Détails d'une facture

Récupère les détails complets d'une facture.

- **URL**: `/api/invoices/{id}/`
- **Méthode**: `GET`
- **Auth requise**: Oui

**Réponse de succès (200 OK)**:
```json
{
  "id": "1",
  "number": "FAC-2025-001",
  "status": "sent",
  "clientId": "1",
  "clientName": "Dupont Construction",
  "clientAddress": "15 rue des Bâtisseurs, 75001 Paris",
  "projectId": "1",
  "projectName": "Villa Moderne",
  "projectAddress": "123 Rue de la Paix, Casablanca",
  "issueDate": "2025-01-15",
  "dueDate": "2025-02-15",
  "paymentTerms": 30,
  "items": [
    {
      "id": "1",
      "type": "chapter",
      "position": 1,
      "designation": "Travaux préparatoires",
      "quantity": 1,
      "unitPrice": 0,
      "vatRate": 20,
      "totalHT": 0,
      "totalTTC": 0
    },
    {
      "id": "2",
      "type": "work",
      "parentId": "1",
      "position": 1,
      "reference": "PREP-001",
      "designation": "Préparation du chantier",
      "description": "Installation et sécurisation de la zone de travail",
      "unit": "forfait",
      "quantity": 1,
      "unitPrice": 500,
      "vatRate": 20,
      "totalHT": 500,
      "totalTTC": 600
    }
  ],
  "notes": "Facture à régler par virement bancaire.",
  "termsAndConditions": "Paiement à 30 jours.",
  "totalHT": 3500,
  "totalVAT": 700,
  "totalTTC": 4200,
  "paidAmount": 0,
  "remainingAmount": 4200,
  "payments": [],
  "quoteId": "devis-123",
  "quoteNumber": "DEV-2025-001",
  "createdAt": "2025-01-15T10:00:00Z",
  "updatedAt": "2025-01-15T10:00:00Z",
  "createdBy": "admin"
}
```

### 3. Créer une facture directe (User Story 5.2)

Crée une nouvelle facture directe sans devis préalable.

- **URL**: `/api/invoices/`
- **Méthode**: `POST`
- **Auth requise**: Oui

**Corps de la requête**:
```json
{
  "clientId": "1",
  "clientName": "Dupont Construction",
  "clientAddress": "15 rue des Bâtisseurs, 75001 Paris",
  "projectId": "1",
  "projectName": "Villa Moderne",
  "projectAddress": "123 Rue de la Paix, Casablanca",
  "issueDate": "2025-01-15",
  "dueDate": "2025-02-15",
  "paymentTerms": 30,
  "items": [
    {
      "type": "product",
      "position": 1,
      "designation": "Matériaux de construction",
      "description": "Fourniture de matériaux divers",
      "unit": "lot",
      "quantity": 1,
      "unitPrice": 8500,
      "vatRate": 20
    }
  ],
  "notes": "Facture pour petite intervention",
  "termsAndConditions": "Paiement à 30 jours."
}
```

**Réponse de succès (201 CREATED)**:
```json
{
  "id": "6",
  "number": "Brouillon",
  "status": "draft",
  "clientId": "1",
  "clientName": "Dupont Construction",
  "clientAddress": "15 rue des Bâtisseurs, 75001 Paris",
  "projectId": "1",
  "projectName": "Villa Moderne",
  "projectAddress": "123 Rue de la Paix, Casablanca",
  "issueDate": "2025-01-15",
  "dueDate": "2025-02-15",
  "paymentTerms": 30,
  "items": [
    {
      "id": "1",
      "type": "product",
      "position": 1,
      "designation": "Matériaux de construction",
      "description": "Fourniture de matériaux divers",
      "unit": "lot",
      "quantity": 1,
      "unitPrice": 8500,
      "vatRate": 20,
      "totalHT": 8500,
      "totalTTC": 10200
    }
  ],
  "notes": "Facture pour petite intervention",
  "termsAndConditions": "Paiement à 30 jours.",
  "totalHT": 8500,
  "totalVAT": 1700,
  "totalTTC": 10200,
  "paidAmount": 0,
  "remainingAmount": 10200,
  "payments": [],
  "createdAt": "2025-01-15T14:20:00Z",
  "updatedAt": "2025-01-15T14:20:00Z",
  "createdBy": "admin"
}
```

### 4. Mettre à jour une facture

Met à jour une facture en brouillon.

- **URL**: `/api/invoices/{id}/`
- **Méthode**: `PUT`
- **Auth requise**: Oui

**Corps de la requête**: Identique à la création de facture

**Réponse de succès (200 OK)**: Identique à la réponse de création de facture

### 5. Supprimer une facture

Supprime une facture en brouillon.

- **URL**: `/api/invoices/{id}/`
- **Méthode**: `DELETE`
- **Auth requise**: Oui

**Réponse de succès (204 NO CONTENT)**

### 6. Valider et émettre une facture (User Story 5.3)

Valide une facture brouillon et lui attribue un numéro définitif.

- **URL**: `/api/invoices/{id}/validate/`
- **Méthode**: `POST`
- **Auth requise**: Oui

**Corps de la requête**:
```json
{
  "issueDate": "2025-01-15"
}
```

**Réponse de succès (200 OK)**:
```json
{
  "id": "6",
  "number": "FAC-2025-005",
  "status": "sent",
  "updatedAt": "2025-01-15T14:25:00Z"
}
```

### 7. Enregistrer un règlement (User Story 5.4)

Enregistre un paiement reçu pour une facture émise.

- **URL**: `/api/invoices/{id}/payments/`
- **Méthode**: `POST`
- **Auth requise**: Oui

**Corps de la requête**:
```json
{
  "date": "2025-01-20",
  "amount": 4200,
  "method": "bank_transfer",
  "reference": "VIR-20250120",
  "notes": "Paiement complet reçu"
}
```

**Réponse de succès (201 CREATED)**:
```json
{
  "payment": {
    "id": "p1",
    "date": "2025-01-20",
    "amount": 4200,
    "method": "bank_transfer",
    "reference": "VIR-20250120",
    "notes": "Paiement complet reçu"
  },
  "invoice": {
    "id": "1",
    "status": "paid",
    "paidAmount": 4200,
    "remainingAmount": 0,
    "updatedAt": "2025-01-20T16:30:00Z"
  }
}
```

### 8. Créer un avoir (User Story 5.5)

Crée un avoir à partir d'une facture émise pour l'annuler.

- **URL**: `/api/invoices/{id}/credit-note/`
- **Méthode**: `POST`
- **Auth requise**: Oui

**Corps de la requête**:
```json
{
  "reason": "Erreur de facturation",
  "issueDate": "2025-01-25",
  "isFullCreditNote": true,
  "selectedItems": []
}
```

**Réponse de succès (201 CREATED)**:
```json
{
  "creditNote": {
    "id": "7",
    "number": "Brouillon",
    "status": "draft",
    "clientId": "1",
    "clientName": "Dupont Construction",
    "issueDate": "2025-01-25",
    "dueDate": "2025-02-25",
    "totalHT": -3500,
    "totalVAT": -700,
    "totalTTC": -4200,
    "originalInvoiceId": "1",
    "notes": "Avoir pour la facture N°FAC-2025-001",
    "createdAt": "2025-01-25T10:00:00Z"
  },
  "originalInvoice": {
    "id": "1",
    "status": "cancelled_by_credit_note",
    "creditNoteId": "7",
    "updatedAt": "2025-01-25T10:00:00Z"
  }
}
```

### 9. Créer une facture depuis un devis (User Story 5.1)

Transforme un devis accepté en facture d'acompte ou totale.

- **URL**: `/api/quotes/{quoteId}/create-invoice/`
- **Méthode**: `POST`
- **Auth requise**: Oui

**Corps de la requête pour facture d'acompte**:
```json
{
  "type": "advance",
  "advancePercentage": 30,
  "issueDate": "2025-01-15",
  "dueDate": "2025-02-15",
  "paymentTerms": 30
}
```

**Corps de la requête pour facture totale**:
```json
{
  "type": "total",
  "issueDate": "2025-01-15",
  "dueDate": "2025-02-15",
  "paymentTerms": 30
}
```

**Réponse de succès (201 CREATED)**:
```json
{
  "id": "8",
  "number": "Brouillon",
  "status": "draft",
  "clientId": "1",
  "clientName": "Dupont Construction",
  "quoteId": "devis-123",
  "quoteNumber": "DEV-2025-001",
  "issueDate": "2025-01-15",
  "dueDate": "2025-02-15",
  "paymentTerms": 30,
  "totalHT": 1050,
  "totalVAT": 210,
  "totalTTC": 1260,
  "paidAmount": 0,
  "remainingAmount": 1260,
  "items": [
    {
      "id": "1",
      "type": "advance_payment",
      "position": 1,
      "designation": "Acompte de 30% sur devis N°DEV-2025-001",
      "quantity": 1,
      "unitPrice": 1050,
      "vatRate": 20,
      "totalHT": 1050,
      "totalTTC": 1260
    }
  ],
  "createdAt": "2025-01-15T11:00:00Z",
  "updatedAt": "2025-01-15T11:00:00Z"
}
```

### 10. Statistiques des factures

Récupère des statistiques sur les factures.

- **URL**: `/api/invoices/stats/`
- **Méthode**: `GET`
- **Auth requise**: Oui

**Réponse de succès (200 OK)**:
```json
{
  "total": 25,
  "draft": 3,
  "sent": 8,
  "overdue": 2,
  "partially_paid": 4,
  "paid": 7,
  "cancelled": 1,
  "cancelled_by_credit_note": 0,
  "totalAmount": 125000,
  "overdueAmount": 15000,
  "paidAmount": 85000,
  "remainingAmount": 40000
}
```

## Codes d'erreur communs

- `400 Bad Request`: Requête invalide (données manquantes ou incorrectes)
- `401 Unauthorized`: Authentification requise
- `403 Forbidden`: Permissions insuffisantes
- `404 Not Found`: Ressource non trouvée
- `409 Conflict`: Conflit (ex: tentative de modification d'une facture déjà émise)
- `422 Unprocessable Entity`: Données valides mais logiquement incorrectes
- `500 Internal Server Error`: Erreur serveur

## Règles métier

### Statuts et transitions autorisées :
- `draft` → `sent` (via validation avec génération automatique du numéro)
- `sent` → `partially_paid` (via paiement partiel)
- `sent` → `paid` (via paiement total)
- `sent` → `overdue` (automatique si échéance dépassée)
- `partially_paid` → `paid` (via paiement complémentaire)
- `sent` → `cancelled_by_credit_note` (via création d'avoir)

### Contraintes métier :
- **Modification** : Seules les factures `draft` peuvent être modifiées ou supprimées
- **Paiements** : Les factures `sent`, `partially_paid` et `overdue` peuvent recevoir des paiements
- **Avoirs** : Seules les factures `sent` peuvent générer des avoirs
- **Devis** : Un devis peut générer plusieurs factures (acompte + solde)
- **Montants** : Les paiements ne peuvent pas dépasser le montant restant dû
- **Calculs** : Tous les totaux sont recalculés automatiquement

### Auto-remplissage des données :

**Priorité des sources de données** :
1. **Données explicites** : Valeurs fournies directement lors de la création/modification
2. **Depuis le devis** : Si une relation `quote` existe, récupération automatique de :
   - `project_name` et `project_address`
   - `client_name` et `client_address` (si pas déjà définis)
   - `quote_number`
3. **Depuis les tiers** : Si une relation `tier` existe, récupération automatique de :
   - `client_name` depuis `tier.nom`
   - `client_address` depuis `tier.adresses` (priorité à l'adresse de facturation)

**Calculs automatiques** :
- `due_date` = `issue_date` + `payment_terms` jours (si non définie)
- `remaining_amount` = `total_ttc` - `paid_amount`
- Totaux HT/TTC recalculés lors de modification des éléments 