# Scénarios de test gRPC – Service Gestion Matériel

Ce document regroupe tous les scénarios de test (CRUD et avancés) pour les services gRPC exposés par l’application.

---

## 1. Pré-requis
- Serveur gRPC lancé (`python manage.py grpcserver`)
- Fichier `.proto` à jour chargé dans votre client gRPC (BloomRPC, Postman, etc.)
- Les IDs utilisés dans les exemples sont à adapter selon vos données réelles

---

## 2. Tests CRUD standards

### A. EquipmentCategory
- **Create**
```json
{
  "name": "Mini-pelle",
  "description": "Engins de terrassement"
}
```
- **List** : (pas de payload)
- **Retrieve**
```json
{
  "id": 1
}
```
- **Update**
```json
{
  "id": 1,
  "name": "Mini-pelle modifiée",
  "description": "Description modifiée"
}
```
- **Destroy**
```json
{
  "id": 1
}
```

### B. Equipment
- **Create**
```json
{
  "name": "MP-015",
  "serial_number": "SN-00015",
  "description": "Mini-pelle 1,5T",
  "is_available": true,
  "category": 1
}
```
- **List** : (pas de payload)
- **Retrieve**
```json
{
  "id": 1
}
```
- **Update**
```json
{
  "id": 1,
  "name": "MP-015 modifiée",
  "serial_number": "SN-00015",
  "description": "Modifiée",
  "is_available": false,
  "category": 1
}
```
- **Destroy**
```json
{
  "id": 1
}
```

### C. EquipmentMovement
- **Create**
```json
{
  "equipment": 1,
  "from_location": "Dépôt",
  "to_location": "Chantier X",
  "notes": "Déplacement initial",
  "end_date": "2024-07-05T18:00:00Z"
}
```
- **List** : (pas de payload)
- **Retrieve**
```json
{
  "id": 1
}
```
- **Update**
```json
{
  "id": 1,
  "from_location": "Dépôt modifié",
  "to_location": "Chantier Y",
  "notes": "Modifié",
  "equipment": 1,
  "end_date": "2024-07-10T18:00:00Z"
}
```
- **Destroy**
```json
{
  "id": 1
}
```

### D. EquipmentReservation
- **Create**
```json
{
  "equipment": 1,
  "context_id": "chantier_X_task_123",
  "start_date": "2024-07-01T08:00:00Z",
  "end_date": "2024-07-05T18:00:00Z",
  "notes": "Réservation pour fondations"
}
```
- **List** : (pas de payload)
- **Retrieve**
```json
{
  "id": 1
}
```
- **Update**
```json
{
  "id": 1,
  "equipment": 1,
  "context_id": "chantier_X_task_123_modifié",
  "start_date": "2024-07-02T08:00:00Z",
  "end_date": "2024-07-06T18:00:00Z",
  "notes": "Modifié"
}
```
- **Destroy**
```json
{
  "id": 1
}
```

---

## 3. Tests avancés (si méthodes custom exposées)

### A. Vérification de disponibilité (CheckAvailability)
```json
{
  "equipment": 1,
  "start_date": "2024-07-01T08:00:00Z",
  "end_date": "2024-07-05T18:00:00Z"
}
```
**Réponse attendue**
```json
{
  "is_available": true
}
```

### B. Transformation d’une réservation en affectation (Fulfill)
```json
{
  "reservation_id": 1,
  "from_location": "Dépôt central",
  "to_location": "Chantier X",
  "end_date": "2024-07-05T18:00:00Z",
  "notes": "Départ matériel"
}
```
**Réponse attendue**
- Mouvement créé, réservation passée à FULFILLED

### C. Conflit de réservation
- Crée une réservation sur une période, puis tente d’en créer une autre sur la même période pour le même équipement (doit échouer).

### D. Cohérence métier
- Vérifie qu’une réservation ne peut être “fulfill” qu’une seule fois.
- Vérifie que l’équipement n’est pas disponible s’il est déjà réservé ou affecté.

---

## 4. Conseils
- Adapte les IDs selon tes données réelles.
- Utilise les méthodes custom si elles sont exposées dans le .proto.
- Pour chaque test, vérifie la réponse et l’état de la base (via List/Retrieve). 




1. Objets à créer pour un test complet
a) Catégorie d’équipement
{
  "name": "Mini-pelle",
  "description": "Engins de terrassement"
}

b) Équipement
{
  "name": "MP-015",
  "serial_number": "SN-00015",
  "description": "Mini-pelle 1,5T",
  "is_available": true,
  "category": <ID de la catégorie créée>
}
c) Autre équipement (pour test de disponibilité multiple)
{
  "name": "MP-018",
  "serial_number": "SN-00018",
  "description": "Mini-pelle 1,8T",
  "is_available": true,
  "category": <ID de la catégorie créée>
}
2. Scénarios de test gRPC
A. Création d’une réservation (succès)
RPC: EquipmentReservationController.Create
{
  "equipment": <ID de MP-015>,
  "context_id": "chantier_X_task_123",
  "start_date": "2024-07-01T08:00:00Z",
  "end_date": "2024-07-05T18:00:00Z",
  "notes": "Réservation pour fondations"
}
Attendu: Statut RESERVED, réservation créée.
Cas disponible (autre équipement, même période) :
{
  "equipment": <ID de MP-018>,
  "start_date": "2024-07-01T08:00:00Z",
  "end_date": "2024-07-05T18:00:00Z"
}
Cas non disponible (même équipement, période chevauchante) :
{
  "equipment": <ID de MP-015>,
  "start_date": "2024-07-03T08:00:00Z",
  "end_date": "2024-07-06T18:00:00Z"
}
Attendu:
MP-018 → is_available: true
MP-015 → is_available: false
C. Création d’une réservation en conflit (doit échouer)
RPC: EquipmentReservationController.Create
{
  "equipment": <ID de MP-015>,
  "context_id": "chantier_Y_task_456",
  "start_date": "2024-07-03T08:00:00Z",
  "end_date": "2024-07-06T18:00:00Z",
  "notes": "Tentative de réservation en conflit"
}
Attendu: Erreur ou message d’indisponibilité.
{
  "reservation_id": <ID de la réservation créée en A>,
  "from_location": "Dépôt central",
  "to_location": "Chantier X",
  "end_date": "2024-07-05T18:00:00Z",
  "notes": "Départ matériel"
}
Attendu:
Mouvement créé, lié à la réservation.
Statut de la réservation → FULFILLED
Statut de l’équipement → indisponible (is_available: false)
E. Liste des réservations
RPC: EquipmentReservationController.List
{}
Attendu:
Liste de toutes les réservations, avec leur statut (RESERVED, FULFILLED, etc.)
F. Création d’une réservation sur un équipement libre
RPC: EquipmentReservationController.Create
{
  "equipment": <ID de MP-018>,
  "context_id": "chantier_Y_task_789",
  "start_date": "2024-07-10T08:00:00Z",
  "end_date": "2024-07-12T18:00:00Z",
  "notes": "Réservation sur équipement libre"
}
Attendu: Succès.
3. Conseils pour le test
Utilise les IDs retournés par les créations précédentes pour les tests suivants.
Teste les cas limites : chevauchement exact, chevauchement partiel, réservation sur un équipement déjà affecté, etc.
Teste la transformation d’une réservation déjà “FULFILLED” (doit échouer).

---

## 5. Tests de logique métier et de robustesse (JSON only)

### Chevauchement de réservation (unicité et disponibilité)
// Réservation 1
{
  "equipment": 1,
  "context_id": "chantier_X_task_123",
  "start_date": "2024-07-01T08:00:00Z",
  "end_date": "2024-07-05T18:00:00Z"
}
// Réservation 2 (chevauchement, doit échouer)
{
  "equipment": 1,
  "context_id": "chantier_X_task_456",
  "start_date": "2024-07-03T08:00:00Z",
  "end_date": "2024-07-06T18:00:00Z"
}
// Réservation sur autre équipement (doit réussir)
{
  "equipment": 2,
  "context_id": "chantier_X_task_789",
  "start_date": "2024-07-01T08:00:00Z",
  "end_date": "2024-07-05T18:00:00Z"
}

### CheckAvailability
{
  "equipment": 1,
  "start_date": "2024-07-01T08:00:00Z",
  "end_date": "2024-07-05T18:00:00Z"
}
// Réponse attendue
{
  "is_available": false
}
{
  "equipment": 2,
  "start_date": "2024-07-01T08:00:00Z",
  "end_date": "2024-07-05T18:00:00Z"
}
// Réponse attendue
{
  "is_available": true
}

### Fulfill (transformation en affectation)
{
  "reservation_id": 1,
  "from_location": "Dépôt central",
  "to_location": "Chantier X",
  "end_date": "2024-07-05T18:00:00Z",
  "notes": "Départ matériel"
}
// Réponse attendue (exemple)
{
  "id": 1,
  "equipment": 1,
  "from_location": "Dépôt central",
  "to_location": "Chantier X",
  "moved_at": "2024-07-01T08:00:00Z",
  "end_date": "2024-07-05T18:00:00Z",
  "reservation": 1
}

// Fulfill sur réservation déjà FULFILLED (doit échouer)
{
  "reservation_id": 1,
  "from_location": "Dépôt central",
  "to_location": "Chantier X",
  "end_date": "2024-07-05T18:00:00Z"
}
// Réponse attendue
{
  "error": "La réservation n'est pas active."
}

### Statuts et transitions
// Annulation
{
  "id": 2,
  "status": "CANCELLED"
}
// Fulfill sur CANCELLED
{
  "reservation_id": 2,
  "from_location": "Dépôt central",
  "to_location": "Chantier X",
  "end_date": "2024-07-05T18:00:00Z"
}
// Réponse attendue
{
  "error": "La réservation n'est pas active."
}
// Expiration
{
  "id": 3,
  "status": "EXPIRED"
}
// Fulfill sur EXPIRED
{
  "reservation_id": 3,
  "from_location": "Dépôt central",
  "to_location": "Chantier X",
  "end_date": "2024-07-05T18:00:00Z"
}
// Réponse attendue
{
  "error": "La réservation n'est pas active."
}

### Unicité stricte
// Deux réservations identiques
{
  "equipment": 1,
  "context_id": "chantier_X_task_123",
  "start_date": "2024-07-01T08:00:00Z",
  "end_date": "2024-07-05T18:00:00Z"
}
{
  "equipment": 1,
  "context_id": "chantier_X_task_123",
  "start_date": "2024-07-01T08:00:00Z",
  "end_date": "2024-07-05T18:00:00Z"
}
// Réponse attendue
{
  "error": "Une réservation identique existe déjà."
}

### Navigation croisée
// Après Fulfill, vérifie la réservation
{
  "id": 1
}
// Réponse attendue
{
  "id": 1,
  "status": "FULFILLED",
  "fulfilled_movement": 1
}
// Vérifie le mouvement
{
  "id": 1
}
// Réponse attendue
{
  "id": 1,
  "reservation": 1
}

### Affectation directe sans réservation
{
  "equipment": 2,
  "from_location": "Dépôt",
  "to_location": "Chantier Y",
  "notes": "Affectation directe",
  "end_date": "2024-07-10T18:00:00Z"
}
// Réponse attendue
{
  "id": 2,
  "reservation": null
}

### Cas limites
// Chevauchement exact
{
  "equipment": 1,
  "start_date": "2024-07-05T18:00:00Z",
  "end_date": "2024-07-10T18:00:00Z"
}
{
  "equipment": 1,
  "start_date": "2024-07-05T18:00:00Z",
  "end_date": "2024-07-10T18:00:00Z"
}
// Réponse attendue
{
  "error": "L'équipement n'est pas disponible sur cette période."
}
// Chevauchement partiel
{
  "equipment": 1,
  "start_date": "2024-07-04T08:00:00Z",
  "end_date": "2024-07-06T18:00:00Z"
}
// Réponse attendue
{
  "error": "L'équipement n'est pas disponible sur cette période."
}
// Réservation sur équipement déjà affecté
{
  "equipment": 1,
  "start_date": "2024-07-01T08:00:00Z",
  "end_date": "2024-07-05T18:00:00Z"
}
// (Créer un mouvement sur la même période, puis tenter la réservation)
// Réponse attendue
{
  "error": "L'équipement n'est pas disponible sur cette période."
}

### Nettoyage et cohérence
// Suppression d'une réservation liée à un mouvement
{
  "id": 1
}
// (Supprimer la réservation, puis Retrieve le mouvement)
// Réponse attendue
{
  "id": 1,
  "reservation": null
}
// Suppression d'un mouvement lié à une réservation
{
  "id": 1
}
// (Supprimer le mouvement, puis Retrieve la réservation)
// Réponse attendue
{
  "id": 1,
  "fulfilled_movement": null
}

---

## 0. Scénario de test complet pas à pas (end-to-end)

### 1. Création d’une catégorie
// Request
{
  "name": "Mini-pelle",
  "description": "Engins de terrassement"
}
// Response attendue
{
  "id": 1,
  "name": "Mini-pelle",
  "description": "Engins de terrassement"
}

### 2. Création d’un équipement
// Request
{
  "name": "MP-021",
  "serial_number": "SN-00021",
  "description": "Mini-pelle 1,8T",
  "is_available": true,
  "category": 1
}
// Response attendue
{
  "id": 1,
  "name": "MP-021",
  "serial_number": "SN-00021",
  "description": "Mini-pelle 1,8T",
  "is_available": true,
  "category": 1
}

### 3. Création d’une réservation
// Request
{
  "equipment": 1,
  "context_id": "chantier_X_task_123",
  "start_date": "2024-07-01T08:00:00Z",
  "end_date": "2024-07-05T18:00:00Z",
  "notes": "Réservation pour fondations"
}
// Response attendue
{
  "id": 1,
  "equipment": 1,
  "context_id": "chantier_X_task_123",
  "start_date": "2024-07-01T08:00:00Z",
  "end_date": "2024-07-05T18:00:00Z",
  "status": "RESERVED",
  "notes": "Réservation pour fondations"
}

### 4. Vérification de disponibilité
// Request
{
  "equipment": 1,
  "start_date": "2024-07-01T08:00:00Z",
  "end_date": "2024-07-05T18:00:00Z"
}
// Response attendue
{
  "is_available": false
}

### 5. Transformation de la réservation en affectation (Fulfill)
// Request
{
  "reservation_id": 1,
  "from_location": "Dépôt central",
  "to_location": "Chantier X",
  "end_date": "2024-07-05T18:00:00Z",
  "notes": "Départ matériel"
}
// Response attendue
{
  "id": 1,
  "equipment": 1,
  "from_location": "Dépôt central",
  "to_location": "Chantier X",
  "moved_at": "2024-07-01T08:00:00Z",
  "end_date": "2024-07-05T18:00:00Z",
  "reservation": 1
}

### 6. Vérification de la réservation après Fulfill
// Request
{
  "id": 1
}
// Response attendue
{
  "id": 1,
  "status": "FULFILLED",
  "fulfilled_movement": 1
}

### 7. Création d’un mouvement direct (sans réservation)
// Request
{
  "equipment": 1,
  "from_location": "Dépôt",
  "to_location": "Chantier Y",
  "notes": "Affectation directe",
  "end_date": "2024-07-10T18:00:00Z"
}
// Response attendue
{
  "id": 2,
  "reservation": null
}
