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
  "start_date": "2024-07-01T08:00:00Z",
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
  "start_date": "2024-07-02T08:00:00Z",
  "end_date": "2024-07-10T18:00:00Z"
}
```
- **Destroy**
```json
{
  "id": 1
}
```

---

## 3. Tests avancés – Affectation directe et chevauchement

### A. Affectation directe sur période libre (succès)
```json
{
  "equipment": 1,
  "from_location": "Dépôt",
  "to_location": "Chantier X",
  "start_date": "2024-07-01T08:00:00Z",
  "end_date": "2024-07-05T18:00:00Z"
}
```

### B. Tentative de double affectation (chevauchement, doit échouer)
- Affectation déjà existante :
```json
{
  "equipment": 1,
  "from_location": "Dépôt",
  "to_location": "Chantier X",
  "start_date": "2024-07-01T08:00:00Z",
  "end_date": "2024-07-05T18:00:00Z"
}
```
- Tentative de nouvelle affectation sur période qui chevauche (doit échouer)
```json
{
  "equipment": 1,
  "from_location": "Dépôt",
  "to_location": "Chantier Y",
  "start_date": "2024-07-03T08:00:00Z",
  "end_date": "2024-07-06T18:00:00Z"
}
```
- **Réponse attendue** : Erreur, l’équipement n’est pas disponible sur cette période.

### C. Affectation sur période adjacente (doit réussir)
- Après la première affectation :
```json
{
  "equipment": 1,
  "from_location": "Dépôt",
  "to_location": "Chantier Z",
  "start_date": "2024-07-05T18:00:00Z",
  "end_date": "2024-07-10T18:00:00Z"
}
```
- **Réponse attendue** : Succès (pas de chevauchement strict)

### D. Affectation sur un autre équipement (doit réussir)
```json
{
  "equipment": 2,
  "from_location": "Dépôt",
  "to_location": "Chantier X",
  "start_date": "2024-07-01T08:00:00Z",
  "end_date": "2024-07-05T18:00:00Z"
}
```
- **Réponse attendue** : Succès

### E. Cas limites
- Chevauchement exact (doit échouer)
```json
{
  "equipment": 1,
  "from_location": "Dépôt",
  "to_location": "Chantier Y",
  "start_date": "2024-07-01T08:00:00Z",
  "end_date": "2024-07-05T18:00:00Z"
}
```
- Chevauchement partiel (doit échouer)
```json
{
  "equipment": 1,
  "from_location": "Dépôt",
  "to_location": "Chantier Y",
  "start_date": "2024-07-04T08:00:00Z",
  "end_date": "2024-07-06T18:00:00Z"
}
```

---

**Adapte les IDs et les dates selon tes données réelles.**

- Pour chaque test, vérifie la réponse et l’état de la base (via List/Retrieve).
- Les erreurs doivent être explicites si l’affectation n’est pas possible (conflit de période).