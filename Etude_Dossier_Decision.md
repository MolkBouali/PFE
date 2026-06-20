# Processus d'Étude de Dossier et Moteur Décisionnel

## 1. Introduction
L'étude de dossier constitue l'étape analytique centrale du système. Elle permet de transformer les données extraites d'un formulaire en une décision administrative et technique basée sur la conformité aéronautique et le consensus entre les directions compétentes.

## 2. Renseignement des Champs et Étude Technique
Cette phase consiste en la saisie et la validation des paramètres techniques nécessaires à l'évaluation de l'obstacle ou de la construction demandée.

### 2.1. Saisie des paramètres DEA
L'agent instructeur renseigne l'entité `EtudeTechnique` avec les données suivantes :
- **Localisation** : Aéroport concerné.
- **Caractéristiques de l'objet** : Type de surface et type d'objet.
- **Données Altimétriques** : 
    - Altitude du sol.
    - Altitude finale.
    - Hauteur demandée.
- **Analyse Spatiale** : Distance par rapport à la piste.

### 2.2. Calcul de Conformité Technique
Le système calcule automatiquement la viabilité technique de la demande :
- **Calcul de l'Écart** : Détermination de la différence entre la hauteur demandée et la hauteur maximale autorisée.
- **Indicateur de Conformité** : Un booléen `conformite` est généré. Si la hauteur demandée excède la limite autorisée, le dossier est marqué comme non-conforme, ce qui influence directement le moteur décisionnel.

---

## 3. Processus de Validation par les Directions
La décision finale ne repose pas uniquement sur des critères techniques, mais sur une validation collégiale impliquant quatre directions stratégiques.

### 3.1. Le Collège des Directions
Chaque direction émet un avis binaire (Accepté/Refusé) via l'entité `DecisionAvis` :
- **DER** : Direction des Études et de la Réglementation.
- **DTA** : Direction du Transport Aérien.
- **DANA** : Direction de la Navigation Aérienne.
- **DNA** : Direction de la Navigation Aérienne (entité de contrôle complémentaire).

### 3.2. Mécanisme de Saisie
L'agent responsable de la synthèse coche les validations (`validation_der`, `validation_dta`, `validation_dana`, `validation_dna`). Ce mécanisme garantit que chaque aspect réglementaire, opérationnel et technique a été revu.

---

## 4. Logique du Moteur Décisionnel
Le moteur décisionnel agrège les résultats de l'étude technique et les validations des directions pour déterminer le type d'avis final.

### 4.1. Critères d'Agrégation
La logique suit une règle de majorité et de conformité :
- **Consensus** : Le système comptabilise le nombre de validations positives. Un seuil critique (généralement $\ge 3$ directions) est requis pour un avis favorable.
- **Interdépendance** : Même avec un consensus, une non-conformité technique majeure peut conduire à un avis défavorable ou conditionné.

### 4.2. Typologie des Avis Générés
Le moteur produit l'un des trois résultats suivants :
- **`FAVORABLE`** : Le dossier est techniquement conforme et a reçu l'accord majoritaire des directions.
- **`FAVORABLE_AVEC_BALISAGE`** : Le dossier est acceptable, mais la sécurité aérienne impose l'installation d'un balisage lumineux ou visuel pour mitiger le risque.
- **`DEFAVORABLE`** : Le dossier est rejeté en raison d'une non-conformité technique critique ou d'une opposition majeure d'une ou plusieurs directions.

---

## 5. Conclusion et Issue du Processus
Une fois la décision actée par le moteur :
1. Un **numéro d'avis** unique est généré.
2. Une **justification** textuelle est attachée à la décision.
3. Le statut du dossier passe à `traite`, déclenchant la génération automatique du document d'avis final.