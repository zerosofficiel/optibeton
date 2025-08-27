# OptiBéton – Application de formulation du béton

OptiBéton est une application interactive de formulation du béton développée avec Streamlit. Elle regroupe trois méthodes reconnues : Dreux-Gorisse, Volumes Absolus et Algorithme Génétique. L’outil permet à l’utilisateur de générer des formulations optimisées en fonction de ses contraintes (résistance, affaissement, Dmax...) et d’exporter les résultats (Excel, TXT).

## 📁 Structure du projet

```
formulation_beton/
├── Home.py                  # Page d'accueil (OptiBéton)
├── logo.png                 # Logo de l'application
├── requirements.txt         # Dépendances nécessaires
├── code_dreux_gorisse_final.py
├── new_formulation_aci.py
├── algorithme genetique co.py
└── pages/
    ├── 1_Dreux_Gorisse.py
    ├── 2_Volumes_Absolus.py
    └── 3_Genetique.py
```

## ▶️ Lancement local

1. Installer les dépendances :

```bash
pip install -r requirements.txt
```

2. Lancer l'application :

```bash
streamlit run Home.py
```

## ☁️ Déploiement en ligne

L'application peut être hébergée gratuitement sur [Streamlit Cloud](https://streamlit.io/cloud).  
Pour cela :
- Créez un dépôt GitHub et ajoutez-y tous les fichiers ci-dessus.
- Sur Streamlit Cloud, connectez votre compte GitHub et déployez le fichier `Home.py`.

## 📦 Fonctions principales

- Choix de la méthode via menu déroulant ou navigation latérale
- Interfaces dédiées par méthode
- Visualisation des résultats (métriques + tableaux)
- Export des résultats (Excel & TXT)
- Support du thème clair/sombre
- Persistance des données entre les actions utilisateur

## 👷 Public cible

Ingénieurs, étudiants en BTP, laboratoires de matériaux, bureaux de contrôle et de formulation.
