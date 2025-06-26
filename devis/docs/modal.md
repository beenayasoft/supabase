# Documentation des Modales - Module de Facturation

Ce document détaille toutes les modales nécessaires pour le module de facturation, leurs champs, leur logique métier et les user stories qu'elles gèrent.

## 🎯 Vue d'ensemble

Le module de facturation nécessite 10 modales principales pour couvrir l'ensemble des fonctionnalités. Chaque modale est conçue pour être performante avec des milliers de lignes de données et optimisée pour l'expérience utilisateur.

## 📋 Liste des Modales

### 1. **CreateInvoiceModal**
**User Story**: US 5.2 - Créer une facture directe

**Rôle**: Création d'une nouvelle facture sans devis préalable

**Trigger**: Bouton "Nouvelle facture" dans Factures.tsx

**Champs et éléments**:

#### Section Client (Obligatoire)
- **Sélection client** (Combobox avec recherche asynchrone)
  - *Pourquoi*: Point de départ obligatoire, source de vérité pour toutes les infos client
  - *Logique*: Recherche dans la base tiers avec pagination pour gérer des milliers de clients
  - *Validation*: Client obligatoire pour poursuivre

#### Section Informations Client (Auto-remplies, lecture seule)
- **Nom du client** (TextField disabled)
  - *Pourquoi*: Confirmation visuelle de la sélection
  - *Source*: `tier.nom` depuis l'API
- **Adresse de facturation** (TextArea disabled)
  - *Pourquoi*: Validation de l'adresse qui apparaîtra sur la facture
  - *Source*: `tier.adresses` (priorité à `facturation=true`)

#### Section Projet/Chantier (Optionnel)
- **Nom du projet** (TextField, 255 char max)
  - *Pourquoi*: Classification et organisation des factures par projet
  - *Logique*: Préparation pour le futur module chantier
- **Adresse du projet** (TextArea, 500 char max)
  - *Pourquoi*: Distinction entre adresse client et adresse de réalisation
- **Référence projet** (TextField, 100 char max)
  - *Pourquoi*: Numéro de dossier, référence interne client

#### Section Conditions (Avec valeurs par défaut)
- **Date d'émission** (DatePicker, défaut: aujourd'hui)
  - *Pourquoi*: Point de départ du délai de paiement
  - *Validation*: Ne peut pas être dans le futur
- **Délai de paiement** (NumberInput, défaut: 30 jours)
  - *Pourquoi*: Calcul automatique de la date d'échéance
  - *Logique*: `due_date = issue_date + payment_terms`
- **Date d'échéance** (DatePicker, calculée automatiquement)
  - *Pourquoi*: Information critique pour le suivi des paiements
  - *Comportement*: Mise à jour automatique si les champs précédents changent

#### Section Contenu (Optionnel)
- **Notes** (TextArea, 1000 char max)
  - *Pourquoi*: Informations spécifiques au projet ou au client
  - *Usage*: Mentions particulières, modalités spéciales
- **Conditions générales** (TextArea, 2000 char max)
  - *Pourquoi*: Aspects juridiques et contractuels
  - *Source*: Peut être pré-rempli depuis les paramètres entreprise

**Endpoints utilisés**:
- **`GET /api/tiers/`** - Recherche asynchrone des clients
  - *Pourquoi*: Combobox de sélection client avec recherche live
  - *Paramètres*: `search`, `page_size=20` pour pagination légère
- **`GET /api/tiers/{id}/`** - Récupération détails client sélectionné
  - *Pourquoi*: Auto-remplissage nom et adresse de facturation
- **`POST /api/invoices/`** - Création de la facture brouillon
  - *Pourquoi*: Sauvegarde de la facture avec statut "draft"
  - *Payload*: Données client, projet, conditions, notes

**Actions**:
- **Créer en brouillon** (Primary button): Crée la facture avec `status="draft"`
- **Annuler** (Secondary button): Ferme la modale sans sauvegarder

**Évolutivité**:
- Recherche client avec debouncing (300ms) pour performances
- Pagination virtuelle sur la liste des clients
- Auto-complétion sur les champs projet basée sur l'historique

---

### 2. **CreateInvoiceFromQuoteModal**
**User Story**: US 5.1 - Créer une facture depuis un devis

**Rôle**: Transformation d'un devis accepté en facture (acompte ou totale)

**Trigger**: Action "Créer facture" depuis un devis ou depuis la vue détail devis

**Champs et éléments**:

#### Section Devis Source (Lecture seule, pour validation)
- **Numéro de devis** (Badge avec statut)
  - *Pourquoi*: Identification claire du document source
  - *Source*: `quote.number` et `quote.status`
- **Client et projet** (Texte formaté)
  - *Pourquoi*: Confirmation des informations qui seront reprises
  - *Format*: "Client: {nom} - Projet: {projet}"
- **Montant total du devis** (Montant formaté)
  - *Pourquoi*: Base de calcul pour l'acompte
  - *Format*: "Total HT: {amount} € / TTC: {amount} €"

#### Section Type de Facture (Radio buttons exclusifs)
- **Facture d'acompte** (Radio avec sous-formulaire conditionnel)
  - *Pourquoi*: Permet de facturer partiellement avant livraison
  - *Cas d'usage*: Avance sur travaux, échelonnement des paiements
- **Facture totale** (Radio button)
  - *Pourquoi*: Facturation complète de tous les éléments du devis
  - *Cas d'usage*: Travaux terminés, paiement à la livraison

#### Section Acompte (Visible uniquement si "Facture d'acompte" sélectionné)
- **Pourcentage d'acompte** (Slider 0-100% + Input numérique)
  - *Pourquoi*: Flexibilité selon les accords commerciaux
  - *Validation*: Entre 1% et 99%
  - *Synchronisation*: Slider et input liés bidirectionnellement
- **Montant de l'acompte** (Calculé en temps réel, lecture seule)
  - *Pourquoi*: Validation immédiate du montant qui sera facturé
  - *Formule*: `(quote.totalHT * percentage / 100)`
  - *Format*: "Acompte: {amount} € HT ({amountTTC} € TTC)"

#### Section Personnalisation (Optionnel, valeurs pré-remplies depuis le devis)
- **Dates et conditions** (Reprises du devis, modifiables)
  - Date d'émission, délai de paiement
  - *Pourquoi*: Adaptation aux spécificités du projet
- **Notes spécifiques** (TextArea)
  - *Pourquoi*: Mentions particulières à cette facture
  - *Pré-remplissage*: Notes du devis si existantes

#### Section Aperçu (Mise à jour en temps réel)
- **Aperçu des éléments qui seront créés** (Liste simplifiée)
  - *Facture totale*: Liste des chapitres principaux
  - *Facture d'acompte*: "Acompte X% sur devis N°XXX"
- **Récapitulatif des montants** (Tableau)
  - Total HT, TVA, TTC
  - *Pourquoi*: Validation finale avant création

**Endpoints utilisés**:
- **`GET /api/quotes/{id}/`** - Récupération complète du devis source
  - *Pourquoi*: Pré-remplissage des informations et validation de cohérence
  - *Usage*: Chargement initial de la modale avec données du devis
- **`POST /api/invoices/from-quote/`** - Création facture depuis devis
  - *Pourquoi*: Endpoint spécialisé pour la conversion devis → facture
  - *Payload*: `quote_id`, `invoice_type` (full/advance), `advance_percentage`
- **`GET /api/quote-items/by_quote/?quote_id={id}`** - Éléments du devis
  - *Pourquoi*: Aperçu des éléments qui seront repris dans la facture
  - *Usage*: Validation et preview du contenu à facturer

**Actions**:
- **Créer la facture** (Primary button): Lance la création avec les paramètres choisis
- **Annuler** (Secondary button): Retour sans création

**Évolutivité**:
- Support des gros devis avec aperçu paginé
- Calculs optimisés côté client pour la réactivité
- Historique des pourcentages d'acompte utilisés

---

### 3. **InvoiceEditorModal**
**User Story**: Toutes les US - Édition complète d'une facture

**Rôle**: Éditeur principal pour modifier une facture brouillon (équivalent de l'éditeur de devis)

**Trigger**: 
- Bouton "Modifier" depuis la liste des factures
- Redirection depuis `handleEditInvoice` dans Factures.tsx
- Création d'une nouvelle facture

**Structure en onglets**:

#### Onglet 1: Informations Générales
**En-tête de la facture**:
- **Statut** (Badge coloré)
  - *Pourquoi*: Indication visuelle de l'état actuel
  - *Couleurs*: Draft (gris), Sent (bleu), Paid (vert), etc.
- **Numéro** (TextField)
  - *Lecture seule*: Si statut ≠ draft
  - *Éditable*: Si draft et numéro personnalisé souhaité
- **Dates importantes** (Groupe de DatePickers)
  - Date d'émission, date d'échéance, délai de paiement
  - *Logique*: Calcul automatique de l'échéance

**Informations client** (Section repliable):
- Reprend les champs de CreateInvoiceModal
- *Modification limitée*: Selon le statut de la facture

#### Onglet 2: Éléments de Facture (Cœur métier)
**Grille d'édition des lignes** (Tableau éditable avancé):
- **Colonnes principales**:
  - Type (Dropdown: Produit, Service, Ouvrage, Chapitre, Section)
  - Désignation (TextField avec auto-complétion)
  - Quantité (NumberInput avec décimales)
  - Prix unitaire (CurrencyInput)
  - Remise % (NumberInput 0-100)
  - TVA (Dropdown des taux: 0%, 7%, 10%, 14%, 20%)
  - Total HT (Calculé automatiquement)
  - Total TTC (Calculé automatiquement)

**Fonctionnalités avancées de la grille**:
- **Hiérarchie parent/enfant** (Indentation visuelle)
  - *Pourquoi*: Organisation en chapitres et sous-éléments
  - *Logique*: Drag & drop pour réorganiser
- **Actions sur les lignes**:
  - Ajouter ligne, Dupliquer ligne, Supprimer ligne
  - Insérer chapitre/section
  - *Pourquoi*: Flexibilité maximale dans la construction
- **Calculs en temps réel**:
  - *Performances*: Debouncing sur les calculs (200ms)
  - *Fiabilité*: Validation des formats numériques

#### Onglet 3: Notes et Conditions
- **Notes internes** (TextArea)
  - *Usage*: Informations pour l'équipe, non visibles sur la facture
- **Conditions générales** (TextArea avec templates)
  - *Usage*: Mentions légales, conditions de paiement
  - *Templates*: Dropdown avec conditions pré-définies

#### Zone de Totaux (Fixe, toujours visible)
**Calculs détaillés** (Mise à jour en temps réel):
- **Sous-totaux par taux de TVA** (Tableau)
  - Base HT, Taux, Montant TVA
  - *Pourquoi*: Détail requis pour la comptabilité
- **Total général**:
  - Total HT, Total TVA, Total TTC
  - *Format*: Gros caractères, mis en valeur

**Endpoints utilisés**:
- **`GET /api/invoices/{id}/`** - Chargement de la facture à éditer
  - *Pourquoi*: Récupération complète des données pour l'édition
  - *Usage*: Initialisation de l'éditeur avec données existantes
- **`GET /api/invoice-items/by_invoice/?invoice_id={id}`** - Éléments de la facture
  - *Pourquoi*: Chargement de la grille d'édition avec hiérarchie
  - *Usage*: Construction de l'arbre des éléments éditables
- **`PUT /api/invoices/{id}/`** - Sauvegarde des modifications générales
  - *Pourquoi*: Mise à jour des informations de la facture (en-tête, notes)
  - *Payload*: Données modifiées de la facture
- **`POST /api/invoice-items/batch_operations/`** - Gestion des éléments en lot
  - *Pourquoi*: Optimisation pour créer/modifier/supprimer plusieurs lignes
  - *Usage*: Toutes les modifications de la grille en une seule requête
- **`GET /api/library/work-items/`** - Auto-complétion des ouvrages
  - *Pourquoi*: Suggestion d'éléments depuis la bibliothèque d'ouvrages
  - *Paramètres*: `search` pour recherche live lors de la saisie

**Actions contextuelles** (Selon le statut):
- **Si statut = draft**:
  - Enregistrer (Secondary), Valider et émettre (Primary)
- **Si statut ≠ draft**:
  - Fermer (lecture seule)

**Évolutivité**:
- **Virtualisation de la grille** pour centaines de lignes
- **Auto-sauvegarde** toutes les 30 secondes
- **Historique des modifications** (undo/redo)
- **Import/Export** vers Excel
- **Templates d'éléments** fréquemment utilisés

---

### 4. **ValidateInvoiceModal**
**User Story**: US 5.3 - Valider et émettre une facture

**Rôle**: Confirmation et validation finale avant émission définitive

**Trigger**: 
- Bouton "Valider et émettre" depuis InvoiceEditorModal
- Action "Envoyer" depuis la liste des factures (`handleSendInvoice`)

**Sections de la modale**:

#### Section Récapitulatif (Lecture seule, pour validation finale)
**Informations essentielles**:
- **Client et montant** (Format carte)
  - Nom du client, projet, montant TTC
  - *Pourquoi*: Les informations les plus critiques en un coup d'œil
- **Échéance et conditions** (Format liste)
  - Date d'échéance calculée, délai de paiement
  - *Pourquoi*: Impact sur la trésorerie, information critique
- **Nombre d'éléments** (Statistic)
  - "X lignes de facturation"
  - *Pourquoi*: Vérification que la facture n'est pas vide

#### Section Numérotation (Information importante)
- **Aperçu du numéro final** (Alert info)
  - "Votre facture recevra le numéro définitif: FAC-2025-XXX"
  - *Pourquoi*: Transparence sur la numérotation automatique
  - *Logique*: Calcul du prochain numéro disponible

#### Section Avertissements (Mise en garde)
- **Message d'irréversibilité** (Alert warning)
  - "⚠️ Une fois émise, cette facture ne pourra plus être modifiée"
  - *Pourquoi*: Sensibilisation aux conséquences légales
- **Implications comptables** (Liste)
  - "Cette action génèrera un numéro définitif"
  - "La facture apparaîtra dans les rapports comptables"
  - *Pourquoi*: Clarification des impacts métier

#### Section Confirmation (Sécurité)
- **Case à cocher obligatoire** (Checkbox)
  - "Je confirme vouloir émettre définitivement cette facture"
  - *Pourquoi*: Éviter les clics accidentels, engagement conscient
  - *Validation*: Bouton "Émettre" désactivé tant que non coché

**Endpoints utilisés**:
- **`GET /api/invoices/{id}/`** - Récupération des données pour validation
  - *Pourquoi*: Affichage du récapitulatif et vérifications pre-validation
  - *Usage*: Chargement initial des informations à valider
- **`GET /api/invoices/next-number/`** - Aperçu du prochain numéro disponible
  - *Pourquoi*: Information transparente sur la numérotation automatique
  - *Usage*: Affichage "FAC-2025-XXX" dans la section numérotation
- **`POST /api/invoices/{id}/validate/`** - Validation et émission définitive
  - *Pourquoi*: Endpoint spécialisé pour la validation avec contrôles métier
  - *Action*: Génération numéro définitif, changement statut vers "sent"
- **`POST /api/invoices/{id}/export/?format=pdf`** - Génération PDF (optionnel)
  - *Pourquoi*: Aperçu ou envoi automatique après validation
  - *Usage*: Si option "aperçu PDF" ou "envoi automatique" activée

**Actions**:
- **Émettre la facture** (Primary button, rouge/warning)
  - *État*: Désactivé par défaut, activé par la checkbox
  - *Action*: Appel à `validateInvoice(invoice.id)`
- **Annuler** (Secondary button): Retour à l'éditeur

**Évolutivité**:
- **Vérifications additionnelles** (TVA, cohérence des montants)
- **Aperçu PDF** en miniature avant validation
- **Envoi automatique** par email après validation (optionnel)

---

### 5. **RecordPaymentModal**
**User Story**: US 5.4 - Enregistrer un règlement

**Rôle**: Saisie rapide et sécurisée d'un paiement reçu

**Trigger**: 
- Action "Enregistrer paiement" depuis la liste (`handleRecordPayment`)
- Bouton dans la vue détail d'une facture

**État actuel**: Déjà implémentée dans le code (RecordPaymentModal.tsx)

**Sections de la modale**:

#### Section Contexte (Lecture seule, rappel)
**Informations de la facture**:
- **Numéro et client** (Badge + texte)
  - *Pourquoi*: Confirmation de la facture concernée
- **Montants importants** (Grid de métriques)
  - Montant total TTC
  - Déjà payé (si paiements partiels)
  - Restant dû (mis en valeur)
  - *Pourquoi*: Contexte pour saisir le bon montant

#### Section Paiement (Formulaire principal)
**Détails du règlement**:
- **Date du paiement** (DatePicker, défaut: aujourd'hui)
  - *Pourquoi*: Traçabilité comptable précise
  - *Validation*: Ne peut pas être dans le futur
- **Montant reçu** (CurrencyInput avec suggestion)
  - *Suggestion*: Pré-rempli avec le restant dû
  - *Validation*: Ne peut pas dépasser le restant dû
  - *Pourquoi*: Éviter les sur-paiements
- **Méthode de paiement** (Select)
  - Options: Virement bancaire, Chèque, Espèces, Carte, Autre
  - *Pourquoi*: Classification pour la comptabilité et le rapprochement bancaire

#### Section Complémentaire (Optionnel)
- **Référence du paiement** (TextField)
  - Numéro de chèque, référence de virement, etc.
  - *Pourquoi*: Rapprochement bancaire facilité
- **Notes** (TextArea)
  - Informations complémentaires sur ce paiement
  - *Pourquoi*: Traçabilité pour les cas particuliers

#### Section Validation (Calculs temps réel)
- **Impact sur la facture** (Alert info)
  - "Après ce paiement: {nouveau_statut}"
  - "Restant dû: {nouveau_restant} €"
  - *Pourquoi*: Validation immédiate de l'impact

**Endpoints utilisés**:
- **`GET /api/invoices/{id}/`** - Récupération contexte de la facture
  - *Pourquoi*: Affichage montants totaux, déjà payés, restant dû
  - *Usage*: Initialisation des métriques de contexte
- **`GET /api/payments/?invoice_id={id}`** - Historique des paiements existants
  - *Pourquoi*: Calcul du restant dû et validation des montants
  - *Usage*: Éviter les sur-paiements, calculs en temps réel
- **`POST /api/invoices/{id}/record-payment/`** - Enregistrement du paiement
  - *Pourquoi*: Endpoint spécialisé avec mise à jour automatique des statuts
  - *Payload*: `amount`, `payment_date`, `payment_method`, `reference`, `notes`
- **`GET /api/invoices/{id}/payment-impact/`** - Simulation impact du paiement
  - *Pourquoi*: Calcul temps réel du nouveau statut et restant dû
  - *Usage*: Section "Impact sur la facture" avec preview

**Actions**:
- **Enregistrer le paiement** (Primary button)
  - *Validation*: Montant > 0 et ≤ restant dû
  - *Action*: Appel à `recordPayment(invoiceId, payment)`
- **Annuler** (Secondary button): Ferme sans sauvegarder

**Évolutivité**:
- **Scan de chèques** (OCR pour montant et date)
- **Import fichiers bancaires** (CSV/OFX)
- **Historique des paiements** de ce client
- **Gestion multi-devises**

---

### 6. **CreateCreditNoteModal**
**User Story**: US 5.5 - Créer un avoir

**Rôle**: Génération d'avoir pour annulation totale ou partielle d'une facture

**Trigger**: 
- Action "Créer avoir" depuis la liste (`handleCreateCreditNote`)
- Bouton dans la vue détail d'une facture émise

**État actuel**: Déjà implémentée dans le code (CreateCreditNoteModal.tsx)

**Sections de la modale**:

#### Section Facture Concernée (Lecture seule, validation)
**Informations source**:
- **Numéro et statut** (Badge avec couleur)
  - *Pourquoi*: Identification claire de la facture à annuler
- **Client et montants** (Carte récapitulative)
  - Client, montant total, montant déjà payé
  - *Pourquoi*: Contexte pour déterminer le type d'avoir

#### Section Type d'Avoir (Radio buttons avec impact visuel)
**Choix du périmètre**:
- **Avoir total** (Radio avec description)
  - "Annule complètement la facture"
  - Impact: Tous les éléments avec montants négatifs
  - *Cas d'usage*: Erreur de facturation, annulation complète
- **Avoir partiel** (Radio avec sous-formulaire)
  - "Annule seulement certains éléments"
  - Impact: Seulement les éléments sélectionnés
  - *Cas d'usage*: Retour de marchandise, correction ponctuelle

#### Section Sélection (Visible si "Avoir partiel" sélectionné)
**Liste des éléments de facture** (Tableau avec checkboxes):
- **Colonnes**: Sélection, Désignation, Quantité, Montant HT, Montant TTC
- **Sélection multiple** avec cases à cocher
- **Calcul temps réel** du montant de l'avoir
- *Pourquoi*: Granularité pour les corrections précises

#### Section Justification (Obligatoire)
- **Raison de l'avoir** (TextArea obligatoire, 500 char max)
  - *Pourquoi*: Exigence légale et comptable
  - *Exemples*: "Erreur de facturation", "Retour marchandise défectueuse"
- **Date d'émission de l'avoir** (DatePicker, défaut: aujourd'hui)
  - *Pourquoi*: Impact sur la comptabilité et les reports

#### Section Aperçu (Validation avant création)
**Impact calculé en temps réel**:
- **Montants de l'avoir** (négatifs, en rouge)
  - Total HT, TVA, TTC de l'avoir
- **Impact sur la facture originale** (Alert warning)
  - "La facture N°XXX sera marquée comme 'Annulée par avoir'"
  - *Pourquoi*: Clarification des conséquences

**Avertissements** (Alert danger):
- "⚠️ Cette action est irréversible"
- "L'avoir générera un numéro définitif"
- *Pourquoi*: Sensibilisation aux conséquences

**Endpoints utilisés**:
- **`GET /api/invoices/{id}/`** - Récupération facture source pour l'avoir
  - *Pourquoi*: Affichage informations complètes et validation des contraintes
  - *Usage*: Section "Facture Concernée" avec numéro, statut, montants
- **`GET /api/invoice-items/by_invoice/?invoice_id={id}`** - Éléments facturés
  - *Pourquoi*: Liste des éléments sélectionnables pour avoir partiel
  - *Usage*: Tableau avec checkboxes pour sélection granulaire
- **`POST /api/invoices/{id}/credit-note-preview/`** - Simulation de l'avoir
  - *Pourquoi*: Calculs temps réel des montants et impact sur facture originale
  - *Payload*: `is_full`, `selected_items` pour preview live
- **`POST /api/invoices/{id}/create-credit-note/`** - Création définitive de l'avoir
  - *Pourquoi*: Génération de l'avoir avec numérotation automatique
  - *Payload*: `is_full_credit_note`, `selected_items`, `reason`, `credit_date`
- **`GET /api/invoices/next-credit-number/`** - Prochain numéro d'avoir
  - *Pourquoi*: Information sur la numérotation (ex: AVO-2025-XXX)
  - *Usage*: Transparence sur le numéro qui sera généré

**Actions**:
- **Créer l'avoir** (Primary button, rouge)
  - *Validation*: Raison obligatoire, au moins un élément sélectionné si partiel
  - *Action*: Appel à `createCreditNote(invoiceId, isFullCreditNote, selectedItems)`
- **Annuler** (Secondary button): Ferme sans création

**Évolutivité**:
- **Templates de raisons** fréquentes
- **Workflow d'approbation** pour gros montants
- **Génération PDF automatique** de l'avoir
- **Notification client** automatique

---

### 7. **InvoiceViewModal**
**User Story**: Support - Consultation détaillée

**Rôle**: Affichage complet en lecture seule d'une facture (tous statuts)

**Trigger**: 
- Action "Voir" depuis la liste (`handleViewInvoice`)
- Clic sur le numéro de facture
- Navigation depuis d'autres modules

**Structure en onglets** (selon le statut):

#### Onglet 1: Détails de la Facture
**En-tête avec statut** (Hero section):
- **Numéro et statut** (Badge coloré grande taille)
- **Dates importantes** (Grid)
  - Émission, échéance, jours de retard (si applicable)
- **Montants principaux** (Métriques)
  - Total TTC, payé, restant dû

**Informations détaillées** (Sections repliables):
- **Client et projet** (Données complètes)
- **Éléments de facturation** (Tableau read-only avec hiérarchie)
- **Notes et conditions** (Texte formaté)

#### Onglet 2: Historique des Paiements
**Liste chronologique**:
- **Tableau des paiements** (si existants)
  - Date, montant, méthode, référence, notes
- **Timeline visuelle** des paiements
- **Solde évolutif** (graphique simple)
- *Pourquoi*: Suivi de l'historique de règlement

#### Onglet 3: Journal d'Activité
**Historique des modifications**:
- **Timeline des événements**:
  - Création, modifications, validation, paiements
  - Qui, quand, quoi
- **Liens vers les documents** liés:
  - Devis d'origine, avoir généré
- *Pourquoi*: Traçabilité complète, audit trail

#### Actions Contextuelles (Selon le statut)
**Toolbar dynamique**:
- **Si draft**: Modifier, Valider, Supprimer
- **Si sent**: Enregistrer paiement, Créer avoir, Modifier (limitée)
- **Si paid**: Télécharger PDF, Voir paiements
- **Si cancelled**: Voir l'avoir, Historique
- **Actions communes**: Télécharger PDF, Imprimer, Partager

**Endpoints utilisés**:
- **`GET /api/invoices/{id}/`** - Données complètes de la facture
  - *Pourquoi*: Affichage détaillé avec toutes les informations
  - *Usage*: Initialisation de l'onglet "Détails de la Facture"
- **`GET /api/invoice-items/by_invoice/?invoice_id={id}`** - Éléments hiérarchiques
  - *Pourquoi*: Tableau read-only avec structure parent/enfant
  - *Usage*: Affichage structuré des lignes de facturation
- **`GET /api/payments/?invoice_id={id}&ordering=-payment_date`** - Historique paiements
  - *Pourquoi*: Timeline chronologique des règlements reçus
  - *Usage*: Onglet "Historique des Paiements" avec timeline visuelle
- **`GET /api/invoices/{id}/activity-log/`** - Journal d'activité
  - *Pourquoi*: Traçabilité complète des actions (création, modif, validation)
  - *Usage*: Onglet "Journal d'Activité" pour audit trail
- **`GET /api/invoices/{id}/related-documents/`** - Documents liés
  - *Pourquoi*: Navigation vers devis d'origine, avoirs générés, etc.
  - *Usage*: Liens contextuels dans le journal d'activité
- **`POST /api/invoices/{id}/export/?format=pdf`** - Export PDF
  - *Pourquoi*: Action "Télécharger PDF" depuis la toolbar
  - *Usage*: Génération à la demande du PDF de la facture

**Évolutivité**:
- **Mode comparaison** avec versions antérieures
- **Export** dans différents formats
- **Commentaires** et annotations
- **Pièces jointes** (justificatifs, photos)

---

### 8. **InvoiceFiltersModal**
**User Story**: Support - Recherche et filtrage avancé

**Rôle**: Filtrage puissant pour la gestion de milliers de factures

**Trigger**: 
- Bouton "Filtres avancés" dans Factures.tsx
- Icône Filter dans la barre d'outils

**Structure en sections** (Accordion):

#### Section 1: Filtres Rapides
**Raccourcis fréquents** (Buttons group):
- Factures du mois, En retard, Brouillons, À encaisser
- *Pourquoi*: Accès rapide aux vues les plus utilisées

#### Section 2: Filtres de Base
**Critères principaux**:
- **Période** (DateRange picker)
  - Date d'émission, d'échéance, de paiement
  - Presets: Ce mois, Trimestre, Année
- **Statuts** (Multi-select avec badges)
  - Sélection multiple des statuts
  - *Pourquoi*: Vues combinées (ex: Émises + Partiellement payées)
- **Montants** (Range slider + inputs)
  - Montant minimum et maximum
  - *Pourquoi*: Focus sur les gros ou petits montants

#### Section 3: Filtres Avancés
**Critères spécialisés**:
- **Client** (Combobox avec recherche)
  - Recherche asynchrone dans la base tiers
  - *Pourquoi*: Suivi par client spécifique
- **Projet** (TextField avec auto-complétion)
  - Basé sur les projets existants
  - *Pourquoi*: Analyse par chantier
- **Méthode de paiement** (Multi-select)
  - Filtrage selon les moyens de règlement
- **Créé par** (Multi-select des utilisateurs)
  - Suivi par commercial, équipe

#### Section 4: Colonnes et Affichage
**Personnalisation de la vue**:
- **Colonnes visibles** (Checkboxes list)
  - Sélection des colonnes à afficher dans le tableau
  - *Pourquoi*: Adaptation selon les besoins utilisateur
- **Tri par défaut** (Select)
  - Critère et sens de tri par défaut
- **Nombre par page** (Select: 10, 25, 50, 100)

#### Section 5: Sauvegarde des Filtres
**Gestion des favoris**:
- **Filtres sauvegardés** (Liste avec actions)
  - Renommer, supprimer, définir par défaut
- **Nouveau filtre** (Input + bouton)
  - Nommage et sauvegarde du filtre actuel
- *Pourquoi*: Efficacité pour les utilisateurs récurrents

**Endpoints utilisés**:
- **`GET /api/tiers/?page_size=50&search=...`** - Recherche clients pour filtrage
  - *Pourquoi*: Combobox "Client" avec recherche asynchrone
  - *Usage*: Filtre par client spécifique avec auto-complétion
- **`GET /api/invoices/filter-values/`** - Valeurs distinctes pour filtres
  - *Pourquoi*: Populate les dropdowns (créateurs, méthodes paiement, projets)
  - *Usage*: Options dynamiques basées sur les données existantes
- **`GET /api/invoices/?{filtres}`** - Application des filtres sur la liste
  - *Pourquoi*: Requête principale avec paramètres de filtrage construits
  - *Usage*: Retour vers Factures.tsx avec filtres appliqués
- **`GET /api/users/current/saved-filters/?module=invoices`** - Filtres sauvegardés
  - *Pourquoi*: Chargement des filtres personnalisés de l'utilisateur
  - *Usage*: Section "Filtres sauvegardés" avec gestion des favoris
- **`POST /api/users/current/saved-filters/`** - Sauvegarde nouveau filtre
  - *Pourquoi*: Persistance des combinaisons de filtres fréquemment utilisées
  - *Payload*: `name`, `filters_config`, `is_default`, `module="invoices"`
- **`PUT /api/users/current/saved-filters/{id}/`** - Modification filtre existant
  - *Pourquoi*: Renommage ou mise à jour des filtres sauvegardés
- **`DELETE /api/users/current/saved-filters/{id}/`** - Suppression filtre
  - *Pourquoi*: Nettoyage des filtres obsolètes

**Actions principales**:
- **Appliquer** (Primary): Active les filtres et ferme la modale
- **Réinitialiser** (Secondary): Remet les filtres par défaut
- **Sauvegarder** (Tertiary): Sauvegarde le filtre actuel
- **Fermer** (Ghost): Ferme sans appliquer

**Évolutivité**:
- **Filtres collaboratifs** (partage entre utilisateurs)
- **Filtres intelligents** (basés sur l'usage)
- **Export des résultats** filtrés
- **Alertes** sur critères personnalisés

---

### 9. **BulkInvoiceActionsModal**
**User Story**: Support - Actions en lot

**Rôle**: Traitement efficace de multiples factures sélectionnées

**Trigger**: 
- Sélection multiple dans la liste + bouton "Actions groupées"
- Checkbox "Tout sélectionner" + actions

**Sections de la modale**:

#### Section Sélection (Validation)
**Récapitulatif des éléments**:
- **Nombre d'éléments** sélectionnés (Metric card)
- **Liste résumée** (Table compacte)
  - Numéro, client, statut, montant
  - Possibilité de désélectionner individuellement
- **Métriques globales** (Stats)
  - Montant total, répartition par statut
- *Pourquoi*: Validation de la sélection avant action

#### Section Actions Disponibles (Selon les statuts)
**Actions par lot** (Cards avec descriptions):

**Pour les factures Draft**:
- **Validation en lot** (Card avec icône)
  - Description: "Valide et émet toutes les factures brouillon"
  - Contrainte: Seulement les factures complètes
- **Suppression en lot** (Card rouge)
  - Description: "Supprime définitivement les brouillons"
  - Sécurité: Confirmation renforcée

**Pour les factures émises**:
- **Export PDF groupé** (Card avec icône)
  - Description: "Génère un ZIP avec tous les PDFs"
- **Envoi par email** (Card avec icône)
  - Description: "Envoie les factures aux clients respectifs"

**Actions universelles**:
- **Export Excel** (Card avec icône)
  - Description: "Exporte la sélection vers Excel"
- **Modification du statut** (Card avec select)
  - Changement de statut en lot (avec restrictions)

#### Section Paramètres (Selon l'action choisie)
**Configuration de l'action** (Formulaire conditionnel):
- **Pour export**: Format, colonnes à inclure
- **Pour envoi email**: Template à utiliser, message personnalisé
- **Pour validation**: Confirmation des numéros générés

#### Section Sécurité (Actions irréversibles)
**Confirmations renforcées**:
- **Case à cocher** pour actions critiques
- **Saisie du mot "CONFIRMER"** pour suppressions
- **Aperçu des conséquences** (Alert warning)
- *Pourquoi*: Protection contre les erreurs de masse

#### Section Progression (Actions longues)
**Feedback temps réel**:
- **Barre de progression** avec pourcentage
- **Log des actions** (succès/erreurs)
- **Possibilité d'annulation** (si supporté)
- **Résumé final** (succès, échecs, raisons)

**Endpoints utilisés**:
- **`GET /api/invoices/?id__in={ids}`** - Récupération des factures sélectionnées
  - *Pourquoi*: Validation de la sélection et affichage du récapitulatif
  - *Usage*: Section "Sélection" avec métriques et liste résumée
- **`POST /api/invoices/bulk-validate/`** - Validation en lot des brouillons
  - *Pourquoi*: Action spécialisée pour émettre plusieurs factures simultanément
  - *Payload*: `invoice_ids[]`, validation avec contraintes métier
- **`DELETE /api/invoices/bulk-delete/`** - Suppression en lot sécurisée
  - *Pourquoi*: Suppression multiple avec vérifications (statut draft uniquement)
  - *Payload*: `invoice_ids[]`, confirmation renforcée requise
- **`POST /api/invoices/bulk-export/?format=pdf`** - Export PDF groupé
  - *Pourquoi*: Génération d'un ZIP avec tous les PDFs des factures
  - *Usage*: Action "Export PDF groupé" avec barre de progression
- **`POST /api/invoices/bulk-email/`** - Envoi email en lot
  - *Pourquoi*: Envoi automatisé aux clients respectifs avec template
  - *Payload*: `invoice_ids[]`, `template_id`, `custom_message`
- **`POST /api/invoices/bulk-export/?format=excel`** - Export Excel
  - *Pourquoi*: Export des données sélectionnées vers Excel
  - *Payload*: `invoice_ids[]`, `columns[]` pour colonnes à inclure
- **`PUT /api/invoices/bulk-update/`** - Modification statut en lot
  - *Pourquoi*: Changement de statut multiple avec restrictions métier
  - *Payload*: `invoice_ids[]`, `new_status`, validation des transitions

**Actions**:
- **Exécuter l'action** (Primary, adaptatif selon la sélection)
- **Annuler** (Secondary): Ferme sans exécuter

**Évolutivité**:
- **Actions personnalisées** (plugins, scripts)
- **Planification** des actions (exécution différée)
- **Template d'actions** fréquentes
- **Gestion des erreurs** avancée avec retry

---

### 10. **DeleteInvoiceModal**
**User Story**: Support - Suppression sécurisée

**Rôle**: Confirmation renforcée pour suppression de facture

**Trigger**: 
- Action "Supprimer" depuis la liste (`handleDeleteInvoice`)
- Bouton supprimer dans l'éditeur (si draft)

**Sections de la modale**:

#### Section Identification (Validation de cible)
**Informations de la facture** (Card en lecture seule):
- **Numéro et statut** (Badge + titre)
- **Client et montant** (Informations principales)
- **Date de création** (Information temporelle)
- *Pourquoi*: Confirmation absolue de l'élément à supprimer

#### Section Vérifications (Contrôles de sécurité)
**Contraintes métier** (Alerts avec icônes):

**Vérification du statut**:
- ✅ "Facture en brouillon: Suppression autorisée"
- ❌ "Facture émise: Suppression interdite"
- *Pourquoi*: Seuls les brouillons peuvent être supprimés

**Vérification des dépendances**:
- **Paiements liés** (Si applicable)
  - "⚠️ Cette facture a reçu des paiements"
  - Action requise: Supprimer les paiements d'abord
- **Avoir associé** (Si applicable)
  - "⚠️ Un avoir fait référence à cette facture"
  - Impact: L'avoir deviendra orphelin

#### Section Impact (Conséquences)
**Ce qui sera supprimé** (Liste avec icônes):
- ✗ La facture et tous ses éléments
- ✗ Les fichiers PDF générés
- ✗ L'historique des modifications
- *Pourquoi*: Transparence totale sur l'impact

**Ce qui sera conservé** (Liste avec icônes):
- ✓ Le client et ses informations
- ✓ Le devis d'origine (si applicable)
- ✓ Les logs système (traces)

#### Section Confirmation (Sécurité maximale)
**Mécanismes de protection**:

**Confirmation textuelle** (Input obligatoire):
- Label: "Pour confirmer, tapez exactement : SUPPRIMER"
- Validation: Comparaison stricte (case sensitive)
- *Pourquoi*: Éviter les clics accidentels

**Délai de réflexion** (Timer de 3 secondes):
- Bouton "Supprimer définitivement" désactivé pendant 3s
- Compte à rebours visible
- *Pourquoi*: Temps de réflexion forcé

**Dernière chance** (Checkbox):
- "Je comprends que cette action est irréversible"
- *Pourquoi*: Engagement conscient de l'utilisateur

**Endpoints utilisés**:
- **`GET /api/invoices/{id}/`** - Récupération informations pour validation
  - *Pourquoi*: Affichage complet des détails de la facture à supprimer
  - *Usage*: Section "Identification" avec numéro, client, montant, date
- **`GET /api/invoices/{id}/deletion-constraints/`** - Vérification contraintes
  - *Pourquoi*: Validation des règles métier (statut, paiements, avoirs liés)
  - *Usage*: Section "Vérifications" avec alertes colorées sur les blocages
- **`GET /api/payments/?invoice_id={id}`** - Vérification paiements liés
  - *Pourquoi*: Contrôle s'il y a des règlements qui bloquent la suppression
  - *Usage*: Alert "⚠️ Cette facture a reçu des paiements"
- **`GET /api/invoices/?original_invoice_id={id}`** - Vérification avoirs
  - *Pourquoi*: Contrôle s'il y a des avoirs qui référencent cette facture
  - *Usage*: Alert "⚠️ Un avoir fait référence à cette facture"
- **`DELETE /api/invoices/{id}/`** - Suppression définitive sécurisée
  - *Pourquoi*: Suppression avec tous les contrôles métier intégrés
  - *Action*: Après validation complète (statut, confirmation textuelle, délai)
- **`POST /api/invoices/{id}/archive/`** - Alternative archivage (évolutivité)
  - *Pourquoi*: Soft delete pour traçabilité sans suppression physique
  - *Usage*: Option future pour remplacer la suppression définitive

**Actions**:
- **Supprimer définitivement** (Danger button, rouge)
  - *État*: Désactivé jusqu'à validation complète
  - *Action*: Suppression avec tous les contrôles
- **Annuler** (Secondary): Ferme sans supprimer

**Évolutivité**:
- **Archivage** au lieu de suppression (soft delete)
- **Audit trail** renforcé
- **Permissions** de suppression par rôle
- **Sauvegarde automatique** avant suppression

---

## 🔄 Flux d'Utilisation Principal

### Scénario 1: Création et émission d'une facture directe
1. **Factures.tsx** → Clic "Nouvelle facture"
2. **CreateInvoiceModal** → Saisie client et infos
3. **InvoiceEditorModal** → Ajout des éléments
4. **ValidateInvoiceModal** → Validation et émission

### Scénario 2: Facturation depuis devis
1. **Module Devis** → Clic "Créer facture"
2. **CreateInvoiceFromQuoteModal** → Type et paramètres
3. **InvoiceEditorModal** → Modifications si nécessaire
4. **ValidateInvoiceModal** → Émission

### Scénario 3: Gestion des paiements
1. **Factures.tsx** → Action "Enregistrer paiement"
2. **RecordPaymentModal** → Saisie du règlement
3. Retour à la liste avec statut mis à jour

### Scénario 4: Correction par avoir
1. **Factures.tsx** → Action "Créer avoir"
2. **CreateCreditNoteModal** → Sélection et justification
3. Génération automatique de l'avoir

## 🎯 Principes de Conception

### Performance et Évolutivité
- **Virtualisation** pour les listes de milliers d'éléments
- **Recherche asynchrone** avec debouncing
- **Calculs optimisés** côté client
- **Cache intelligent** des données fréquentes

### Expérience Utilisateur
- **Feedback temps réel** sur tous les calculs
- **Validations proactives** avec messages clairs
- **Raccourcis clavier** pour les actions fréquentes
- **Auto-sauvegarde** pour éviter les pertes

### Sécurité et Fiabilité
- **Confirmations renforcées** pour actions critiques
- **Validations métier** strictes
- **Gestion d'erreurs** avec messages explicites
- **Audit trail** complet

### Maintenabilité
- **Composants réutilisables** entre modales
- **État partagé** via Context/Redux
- **Tests automatisés** sur chaque modale
- **Documentation** technique complète

Cette architecture de modales permet une gestion complète et efficace du module de facturation, avec une évolutivité pensée pour des milliers d'éléments et une expérience utilisateur optimale.
