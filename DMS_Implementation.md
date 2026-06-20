# Implémentation du Traitement des Coordonnées Géographiques (Cycle DMS $\rightarrow$ DD)

## 1. Introduction
Dans le cadre de l'automatisation de l'extraction de données à partir de formulaires papier, la récupération des coordonnées géographiques représente un défi majeur en raison de la diversité des formats utilisés (Degrés Minutes Secondes, Degrés Minutes Décimales, Degrés Décimaux) et des erreurs inhérentes à la reconnaissance optique de caractères (OCR). 

Cette section décrit l'implémentation du pipeline de traitement conçu pour normaliser, détecter et convertir ces coordonnées en un format standard exploitable par les systèmes d'information géographique (SIG).

## 2. Architecture du Cycle de Traitement
Le système implémente un cycle de traitement séquentiel composé de cinq étapes clés, garantissant la transition d'un texte brut potentiellement bruité vers une donnée numérique précise.

### Flux de données :
`Texte Brut (OCR)` $\rightarrow$ `Normalisation` $\rightarrow$ `Détection du Format` $\rightarrow$ `Validation & Parsing` $\rightarrow$ `Conversion DD`

---

## 3. Détails Techniques de l'Implémentation

### 3.1. Normalisation et Prétraitement
L'étape de normalisation (`normaliser_dms`) vise à corriger les erreurs de substitution classiques de l'OCR. Elle utilise des remplacements de caractères pour restaurer la sémantique des coordonnées :
- **Symboles :** Correction du symbole degré (ex: `*` $\rightarrow$ `°`).
- **Confusion numérique :** Correction des lettres confondues avec des chiffres (ex: `O` ou `o` $\rightarrow$ `0`, `l` ou `I` $\rightarrow$ `1`).
- **Ponctuation :** Uniformisation des guillemets et des séparateurs (ex: `;` $\rightarrow$ `'`).

### 3.2. Détection Automatique du Format
La fonction `detecter_format` analyse la structure de la chaîne normalisée pour identifier le format d'entrée. L'algorithme suit une hiérarchie de priorité basée sur des expressions régulières (Regex) :

1. **Format DMS (Degrés, Minutes, Secondes)** : Recherche de motifs incluant des degrés, minutes, secondes et une direction (N, S, E, W).
2. **Format DM (Degrés, Minutes Décimales)** : Identification des coordonnées avec minutes sous forme décimale.
3. **Format DD (Degrés Décimaux)** : Reconnaissance des nombres flottants simples accompagnés ou non d'une direction.

#### Analyse Détaillée des Expressions Régulières (Regex)
La robustesse du système repose sur des motifs Regex conçus pour tolérer le "bruit" généré par l'OCR. Par exemple, le pattern DMS utilisé est le suivant :

`(\d{1,2})\s*[°\s,]*\s*(\d{1,2})\s*['\s,]*\s*(\d{1,2}(?:[.,]\d+)?)\s*[\"\s,]*\s*([NS])`

**Décomposition du motif :**
- **Capture des Degrés `(\d{1,2})`** : Capture 1 à 2 chiffres.
- **Séparateurs Flexibles `\s*[°\s,]*\s*`** : Permet la présence ou l'absence du symbole degré (`°`), d'espaces ou de virgules, évitant ainsi que le système ne rejette la donnée si l'OCR a mal interprété le symbole.
- **Capture des Minutes `(\d{1,2})`** : Capture 1 à 2 chiffres.
- **Capture des Secondes `(\d{1,2}(?:[.,]\d+)?)`** : Capture un nombre pouvant être entier ou décimal (avec point ou virgule), permettant une précision accrue.
- **Direction `([NS])`** : Capture strictement la direction cardinale.

Une approche similaire est appliquée pour la longitude (permettant jusqu'à 3 chiffres pour les degrés et les directions `E` ou `W`).

Cette stratégie de "tolérance syntaxique" permet d'extraire des coordonnées même lorsque la ponctuation est incomplète ou erronée, transformant un texte comme `"36 * 52 ' 28,42 N"` en une structure de données rigoureuse.

### 3.3. Parsing et Validation Sémantique
Une fois le format identifié, le système procède à l'extraction des composants et à leur validation (`valider_dms`). Cette étape est cruciale pour rejeter les données aberrantes :
- **Plages de valeurs :** 
    - Latitude $\in [0, 90^\circ]$
    - Longitude $\in [0, 180^\circ]$
    - Minutes et Secondes $\in [0, 60[$
- **Direction :** Vérification de la cohérence du quadrant (N/S pour la latitude, E/W pour la longitude).

### 3.4. Conversion vers le Format Degrés Décimaux (DD)
La conversion finale (`_dms_to_dd`) transforme les coordonnées validées en un nombre flottant unique selon la formule mathématique suivante :

$$\text{DD} = \text{Degrés} + \frac{\text{Minutes}}{60} + \frac{\text{Secondes}}{3600}$$

Le signe final est déterminé par la direction : le résultat est négatif si la direction est **Sud (S)** ou **Ouest (W)**.

---

## 5. Gestion des Échecs et Demande de Complément

Le pipeline de traitement intègre un mécanisme de repli pour les cas où l'extraction automatique échoue ou produit des résultats ambigus. Cette étape assure qu'aucune donnée erronée n'est injectée dans le système.

### 5.1. Workflow de demande de complément
Lorsqu'une coordonnée ne peut être validée par le processus de parsing (`valider_dms`), le dossier est marqué avec le statut `en_attente_complement`. Cela déclenche la possibilité de générer un document officiel de demande de complément.

### 5.2. Logique de Génération Technique
La génération du document est orchestrée par le `PDFService` selon la logique suivante :
- **Utilisation de Templates** : Le système s'appuie sur un modèle Word (`complement_template.docx`) contenant des balises de substitution.
- **Injection Dynamique** : Les informations spécifiques au dossier (Numéro de dossier et Nom du demandeur) sont extraites de la base de données et injectées dans le template via des placeholders (ex: `{{NUMERO_DOSSIER}}`).
- **Objectif Sémantique** : Le document généré informe l'usager de la non-conformité des données fournies et exige explicitement la soumission de coordonnées respectant strictement la norme **DMS**.
- **Traçabilité** : Chaque document produit est enregistré dans la table `DocumentGenere` avec le type `COMPLEMENT_DMS`, permettant un suivi rigoureux de l'historique des échanges avec le demandeur.

---

## 6. Conclusion
L'implémentation de ce cycle complet, allant de la normalisation OCR à la gestion des échecs par la demande de complément, permet de transformer un processus d'extraction fragile en un système robuste. En combinant la flexibilité des expressions régulières, la rigueur de la validation sémantique et un circuit de correction administratif, le pipeline assure l'intégrité absolue des données géographiques, minimisant ainsi les erreurs de positionnement dans la base de données finale.
