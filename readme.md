### Instructions réformulées
- **Place-toi dans le dossier `supabase` avant d'exécuter une commande concernant le backend Django.**  
- **Vérifie que tu es bien dans le dossier `beena` avant de lancer toute commande liée au frontend (React + Tailwind).**  
- **Suis strictement les directives sans ajouter de fonctionnalités supplémentaires.** Tu peux cependant proposer des suggestions à l’utilisateur et attendre son approbation avant d’implémenter quoi que ce soit.  
- **Facilite la connexion entre le frontend et le backend via les API exposées par les modules concernés.**  

Utilise tous tes outils disponibles en mode chat et veille à exécuter chaque étape avec rigueur et méthode. 🚀
.......................................................................................................................
Prompt 
imagine une user story qui utilise l'endpoint crée, pour que je puisse voir a chaque moment et visualiser un cas reel d'utilisation selon
le template suivante :
.........................................................................................................................................
Template
..........................................................................................................................
### User Story illustrant les endpoints d'authentification
#### 1. Inscription d’un nouvel utilisateur  
**Endpoint:** `POST /api/auth/register/`  
##### Scénario  
Jean, entrepreneur en bâtiment, découvre l’application Benaya et décide de créer un compte pour gérer ses chantiers.  

##### Étapes utilisateur  
1. Il accède à la page d'authentification et clique sur "Créer un compte".  
2. Il remplit le formulaire avec ses informations :  
   - Email : `jean@batiment-pro.fr`  
   - Mot de passe : `Secure123!`  
   - Confirmation du mot de passe : `Secure123!`  
   - Nom : `Jean`  
   - Prénom : `Dupont`  
   - Entreprise : `Bâtiment Pro`  
3. Il clique sur "Créer mon compte".  

##### Requête API  
```http
POST /api/auth/register/
Content-Type: application/json
```
```json
{
  "email": "jean@batiment-pro.fr",
  "username": "jean.dupont",
  "password": "Secure123!",
  "password2": "Secure123!",
  "first_name": "Jean",
  "last_name": "Dupont",
  "company": "Bâtiment Pro"
}
```
##### Réponse attendue  
```json
{
  "user": {
    "id": 1,
    "email": "jean@batiment-pro.fr",
    "username": "jean.dupont",
    "first_name": "Jean",
    "last_name": "Dupont",
    "company": "Bâtiment Pro"
  },
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```
##### Résultat attendu  
Jean est automatiquement connecté et redirigé vers le tableau de bord de l’application. Son token d’accès est stocké dans le localStorage du navigateur pour les futures requêtes authentifiées.

---

#### 2. Connexion d’un utilisateur existant  
**Endpoint:** `POST /api/auth/login/`  
##### Scénario  
Le lendemain, Jean revient sur l’application et doit se connecter.  

##### Étapes utilisateur  
1. Il visite la page d'authentification.  
2. Il saisit :  
   - Email : `jean@batiment-pro.fr`  
   - Mot de passe : `Secure123!`  
3. Il clique sur "Se connecter".  

##### Requête API  
```http
POST /api/auth/login/
Content-Type: application/json
```
```json
{
  "email": "jean@batiment-pro.fr",
  "password": "Secure123!"
}
```
##### Réponse API  
```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```
Cette structure t'offre une meilleure lisibilité et facilite la visualisation des cas réels. Besoin d'ajouter d'autres scénarios ? 😊
