Epic : Facturation et Suivi des Paiements
User Story 5.1 : Créer une facture à partir d'un devis
Titre : [Invoicing] Créer une facture d'acompte ou de solde depuis un devis accepté
Description :
En tant qu' utilisateur (Administratif ou Gérant),
Je veux pouvoir transformer un devis accepté en facture en un clic, en choisissant s'il s'agit d'un acompte ou du solde,
Afin de facturer rapidement et sans erreur ce qui a été vendu.
Critères d'Acceptation :
Sur un devis au statut "Accepté", le bouton "Créer une facture" est visible.
En cliquant, une fenêtre me demande de choisir entre "Facture d'acompte" et "Facture totale/de solde".
Si je choisis "Acompte", je peux saisir un pourcentage. Une facture est créée avec une seule ligne pour cet acompte.
Si je choisis "Totale/Solde", une facture est créée reprenant toutes les lignes du devis.
Si un acompte a déjà été facturé pour ce devis, la facture de solde inclut automatiquement une ligne de déduction de l'acompte versé.
La facture est créée au statut "Brouillon".


User Story 5.2 : Créer une facture directe
Titre : [Invoicing] Créer une facture directe (sans devis préalable)
Description :
En tant qu' utilisateur,
Je veux pouvoir créer une facture de zéro pour des petites interventions ou de la vente de matériel,
Afin de ne pas être obligé de passer par un devis pour des cas simples.
Critères d'Acceptation :
Un bouton "Créer une facture" sur la page de liste des factures me permet de créer une facture vierge.
Je peux sélectionner un client depuis le Module 3.
Je peux ajouter manuellement des lignes de prestation avec description, quantité, prix unitaire HT et taux de TVA.
La facture est créée au statut "Brouillon".


User Story 5.3 : Valider et émettre une facture
Titre : [Invoicing] Valider et finaliser une facture
Description :
En tant qu' utilisateur,
Je veux pouvoir valider une facture en brouillon pour la rendre définitive et infalsifiable,
Afin de respecter la loi et de pouvoir l'envoyer à mon client.
Critères d'Acceptation :
Sur une facture au statut "Brouillon", j'ai un bouton "Valider et émettre".
En cliquant, le système attribue un numéro de facture définitif et séquentiel (selon le format du Module 2).
Le statut de la facture passe à "Émise".
La facture ne peut plus être modifiée ni supprimée.
Un bouton "Générer PDF" me permet d'obtenir le document officiel.


User Story 5.4 : Enregistrer des règlements
Titre : [Invoicing] Enregistrer les règlements reçus pour une facture
Description :
En tant qu' utilisateur,
Je veux pouvoir enregistrer les paiements (partiels ou totaux) que je reçois de mes clients,
Afin de suivre précisément l'état de ma trésorerie et les factures en attente.
Critères d'Acceptation :
Sur une facture "Émise", un bouton "Enregistrer un règlement" est disponible.
Je peux saisir le montant du règlement, la date et le mode de paiement.
Le "Restant dû" de la facture est mis à jour après chaque règlement enregistré.
Si le "Restant dû" est de 0, le statut de la facture passe automatiquement à "Payée".
Si le "Restant dû" est positif mais inférieur au total, le statut passe à "Payée partiellement".
Si la date d'échéance est dépassée et que la facture n'est pas "Payée", son statut passe à "En retard".


User Story 5.5 : Créer un avoir pour annuler une facture
Titre : [Invoicing] Créer un avoir pour corriger ou annuler une facture émise
Description :
En tant qu' utilisateur,
Je veux pouvoir créer un avoir à partir d'une facture déjà émise,
Afin de pouvoir annuler une erreur comptable de manière légale.
Critères d'Acceptation :
Sur une facture "Émise", un bouton "Créer un avoir" est disponible.
Cliquer sur ce bouton crée un nouveau document de type "Avoir" qui est une copie de la facture avec des montants négatifs.
L'avoir est créé en "Brouillon" et je peux le valider comme une facture normale.
Une fois l'avoir validé, il est lié à la facture d'origine et le statut de cette dernière passe à "Annulée".
