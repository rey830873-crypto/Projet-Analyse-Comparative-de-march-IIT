<<<<<<< HEAD
# Projet-Analyse-Comparative-de-march-IIT
=======
# Comparateur de marché à Abidjan

**Projet de DA Python — L2 Computer Science — séance 3**

Cette application compare les prix de trois enseignes fictives : **Marché Lagune**, **Baobab Shop** et **Comptoir Ivoire**. Elle aide à répondre à une question simple : *pour un produit donné, quelle enseigne propose le meilleur prix réellement payable ?*

> Les enseignes et les prix sont fictifs. Ils ont été créés pour l'exercice et ne représentent aucun commerce réel.

## Le projet en quelques mots

Chaque enseigne fournit ses informations dans un format différent et écrit les noms des produits à sa façon. Le programme lit ces fichiers, retrouve les produits correspondants dans un catalogue commun, écarte les offres qui ne sont pas achetables, puis calcule les différences de prix.

L'application affiche les résultats dans plusieurs espaces :

- une vue d'ensemble des résultats ;
- un comparatif filtrable par catégorie ;
- le détail du panier de rentrée ;
- l'évolution des prix autour du Black Friday ;
- un journal qui explique les corrections et exclusions.

Le programme ne lance pas l'analyse automatiquement à l'ouverture. Il faut cliquer sur **Lancer l'analyse**. Ainsi, l'utilisateur choisit le moment où les fichiers sont lus et calculés.

## Démarrer l'application

Ouvrez le dossier du projet dans VS Code, ouvrez un terminal à cet emplacement, puis exécutez ces commandes dans PowerShell :

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

La première commande crée un environnement Python isolé pour ce projet. La deuxième l'active. La troisième installe les bibliothèques requises. La dernière ouvre la fenêtre de l'application.

Si `.venv` existe déjà, il n'est pas nécessaire de le recréer. Activez-le, puis lancez `python main.py`.

Dans la fenêtre :

1. Vérifiez que le dossier de données indiqué est **Data**. Pour choisir un autre dossier, cliquez sur **Choisir le dossier**.
2. Cliquez sur **Lancer l'analyse**.
3. Utilisez le menu de gauche pour consulter les résultats.
4. Dans **Comparatif des prix**, choisissez Smartphone, Informatique ou Électroménager pour afficher une catégorie à la fois.
5. Cliquez sur **Exporter le comparatif en CSV** pour enregistrer le tableau.

## Les fichiers de l'exercice

Les cinq fichiers d'entrée se trouvent dans le dossier `Data/`.

| Fichier | À quoi il sert | Comment le programme le lit |
|---|---|---|
| `catalogue_reference.csv` | Donne les 30 produits de référence, leur identifiant, leur nom, leur catégorie et leur marque. | CSV avec séparateur virgule, lu avec pandas. |
| `marche_lagune.csv` | Donne les désignations, prix et disponibilités de Marché Lagune. | CSV français avec séparateur point-virgule, lu avec pandas. Le prix inclut la livraison. |
| `baobab_shop.json` | Contient les articles, leurs prix, les frais de livraison et le stock de Baobab Shop. | JSON lu avec le module `json` de Python. |
| `comptoir_ivoire.xlsx` | Contient les prix catalogue, remises et quantités en rayon du Comptoir Ivoire. | Classeur Excel lu avec `openpyxl`. Les en-têtes sont à la ligne 3 et les articles commencent à la ligne 4. |
| `historique_prix.csv` | Contient les prix observés du 1er novembre 2025 au 31 octobre 2026. | CSV lu avec pandas. Les produits ont déjà un identifiant commun, comme P01 ou P14. |

Les trois CSV sont lus avec `pandas.read_csv`. Le comparatif est exporté avec `DataFrame.to_csv`. Le projet n'utilise pas le module standard `csv` de Python.

Un autre dossier de données peut être choisi avec le bouton **Choisir le dossier**.

## Fichiers créés après l'analyse

Les fichiers d'origine dans `Data/` ne sont jamais modifiés. À chaque clic sur **Lancer l'analyse**, le programme crée ou met à jour des copies traitées afin que l'on puisse examiner le résultat du nettoyage séparément des fichiers bruts :

| Emplacement | Contenu |
|---|---|
| `donnees_nettoyees/offres_normalisees.csv` | Offres des trois enseignes réunies dans le même format, avec identifiant, catégorie, prix, disponibilité et indication si le prix peut être utilisé. |
| `donnees_nettoyees/historique_nettoye.csv` | Lignes valides de l'historique, avec dates, enseignes, identifiants et prix harmonisés. |
| `logs/journal_nettoyage.txt` | Journal lisible avec une entrée par problème, correction ou étape de chargement signalée. |
| `logs/journal_nettoyage.csv` | Le même journal sous forme de tableau pour l'ouvrir ou le filtrer dans un tableur. |
| `logs/nettoyage.log` | Journal technique horodaté de l'exécution. Il complète le journal lisible. |
| `exports/comparatif_prix.csv` | Comparatif complet enregistré lorsque l'utilisateur choisit **Exporter le comparatif en CSV**. Le sélecteur propose `exports/` par défaut. |

Ces sorties sont recréées à chaque analyse avec les données sélectionnées. Les fichiers bruts restent dans `Data/` pour permettre de refaire les calculs ou de vérifier le nettoyage.

## Comment le programme transforme les fichiers en comparatif

### 1. Chargement

Le programme ouvre le catalogue de référence, puis les trois fichiers des enseignes. Les informations des enseignes sont converties dans une structure commune appelée **offre**. Une offre contient notamment l'identifiant du produit, son nom de référence, l'enseigne, le prix payé et l'état de disponibilité.

Cette structure commune permet de comparer les trois enseignes même si les fichiers d'origine n'ont ni le même format ni les mêmes colonnes.

### 2. Normalisation et rapprochement des produits

Le catalogue sert de dictionnaire commun. Par exemple, une ligne nommée « Galaxy A15 128GB - Samsung » peut être reliée à **P01 — Samsung Galaxy A15 128 Go**.

Pour retrouver les correspondances, le programme met les noms en minuscules, retire les accents et la ponctuation, harmonise certaines unités (par exemple `GB` et `Go`) et reconnaît quelques variantes françaises, anglaises ou fautives. Il compare ensuite le nom obtenu aux noms du catalogue.

Si aucun rapprochement n'est assez convaincant, l'article est signalé dans le journal et il n'entre pas dans les calculs. Avec les fichiers actuellement fournis, l'interface indique **0 article à rapprocher manuellement**.

### 3. Nettoyage et disponibilité

Le programme ne considère pas tout prix écrit dans un fichier comme un prix que le client peut payer.

- **Marché Lagune** : « Rupture » signifie que l'offre ne peut pas être choisie. « En stock » et « Stock limité » restent admissibles si le prix est exploitable. La livraison est déjà comprise dans le prix.
- **Baobab Shop** : le prix payé est `amount + delivery_fee`. L'offre est admissible si le stock est supérieur à zéro et si la devise est XOF/FCFA.
- **Comptoir Ivoire** : le prix payé est le prix catalogue diminué du pourcentage de remise. Une quantité en rayon égale à zéro rend l'offre indisponible.
- **Prix manquant, nul ou négatif** : l'offre ne peut pas gagner le comparatif et le problème est signalé.
- **Prix très éloigné** : si le prix d'une offre dépasse trois fois la médiane des offres relevées pour ce même produit, il est signalé comme anomalie probable et mis à l'écart. C'est une règle de détection à vérifier, pas la preuve certaine d'une erreur.

> Exemple des fichiers fournis : le Tecno Spark 20 de Marché Lagune affiche un prix de 779 000 FCFA, très supérieur aux offres comparables. Le programme le signale et l'écarte. Dans le panier, le prix correspondant est donc affiché par un tiret et le panier de Marché Lagune est marqué incomplet pour ce produit.

Les problèmes sont présentés dans l'onglet **Journal de nettoyage** et enregistrés dans les fichiers de `logs/`. Les versions TXT et CSV sont destinées à la lecture et à la vérification ; le fichier `.log` conserve en plus l'heure des opérations.

### 4. Calcul d'une ligne du comparatif

Pour chaque identifiant produit, le programme rassemble les offres disponibles. Il ne crée une ligne comparable que si au moins deux enseignes ont un prix admissible.

Exemple : si Baobab Shop demande 104 000 FCFA et Comptoir Ivoire 92 990 FCFA pour le même produit, le prix minimum est 92 990 FCFA. L'écart est :

```text
Écart en FCFA = prix maximum - prix minimum
Écart en % = (écart en FCFA / prix minimum) × 100
```

Dans cet exemple, l'écart est de 11 010 FCFA, soit environ 11,8 % du prix le plus bas. La colonne **Moins cher** désigne l'enseigne proposant le prix admissible minimum. Les offres en rupture ou sans prix exploitable ne peuvent pas gagner.

Le comparatif complet peut être exporté en CSV. Le filtre par catégorie ne change pas les calculs : il sert seulement à rendre les lignes plus faciles à lire.

### 5. Synthèse et produits où comparer

La vue d'ensemble indique :

- combien de produits de référence ont été chargés ;
- combien d'offres d'enseignes ont été lues ;
- combien de produits ont au moins deux offres admissibles ;
- combien de fois chaque enseigne est la moins chère ;
- l'écart moyen de chaque enseigne par rapport au prix minimum, sur les produits comparables où elle a une offre admissible.

Le tableau des trois économies potentielles est classé selon **l'écart en pourcentage**. Il montre également l'écart en FCFA. Un produit ayant le plus grand écart en pourcentage n'est pas nécessairement celui dont l'écart en FCFA est le plus grand.

### 6. Panier de rentrée

Le panier demandé est :

| Produit | Identifiant | Quantité |
|---|---:|---:|
| Tecno Spark 20 | P04 | 1 |
| Lenovo IdeaPad 3 | P12 | 1 |
| Clé USB SanDisk | P14 | 2 |
| Disque dur Seagate | P15 | 1 |
| Micro-ondes Samsung | P28 | 1 |

Le tableau du panier montre le prix unitaire par enseigne et le meilleur choix pour chaque ligne. La quantité est prise en compte dans le coût total : la clé USB est donc comptée deux fois.

Si une enseigne ne peut pas fournir un des articles, son panier est marqué **Incomplet** et le produit manquant est nommé. Le total optimisé prend chaque article dans l'enseigne admissible la moins chère. Si un article est indisponible dans les trois enseignes, le total optimisé est présenté comme partiel.

Avec les données actuellement fournies, les captures montrent un panier complet à **491 500 FCFA** chez Baobab Shop et **484 075 FCFA** chez Comptoir Ivoire. Marché Lagune est incomplet pour le Tecno Spark 20. En répartissant les achats entre les offres admissibles les moins chères, le total est **477 575 FCFA**.

### 7. Historique et Black Friday

L'historique contient **20 876 observations**. Pour chaque enseigne, le programme calcule la moyenne des prix présents dans le fichier pour l'année, puis la moyenne des observations du **24 au 30 novembre 2025**. Il affiche la différence en pourcentage entre la moyenne Black Friday et la moyenne annuelle.

Dans les données de l'exercice, les moyennes du Black Friday sont environ 11,16 % plus basses chez Marché Lagune et 11,59 % plus basses chez Baobab Shop. Chez Comptoir Ivoire, elles sont environ 3,72 % plus élevées.

Les nombres de lignes affichés rappellent que les enseignes n'ont pas toutes la même fréquence de mise à jour. Comptoir Ivoire a moins d'observations, car ses prix changent environ une fois par semaine. Le calcul est une moyenne des lignes disponibles pour chaque enseigne ; il ne transforme pas les lignes hebdomadaires du Comptoir en observations quotidiennes.

### 8. Temps de calcul et structures de données

Une recherche naïve pourrait reparcourir les 20 876 lignes de l'historique à chaque demande. Le programme construit plutôt un dictionnaire en mémoire dont la clé est le couple `(enseigne, produit_id)`. Chaque clé donne accès aux observations correspondantes.

- Construire le dictionnaire demande un seul parcours de l'historique : **O(n)**, où `n` est le nombre de lignes.
- Rechercher une clé dans un dictionnaire prend en moyenne **O(1)**.
- L'index et l'historique occupent une mémoire proportionnelle au nombre de lignes : **O(n)**.
- La comparaison des offres courantes parcourt les offres et les groupes de produits, plutôt que de refaire une recherche complète dans l'historique pour chaque produit.
- Pour calculer les moyennes annuelles et Black Friday, le programme récupère les séries dans l'index puis examine les observations de chaque enseigne. Cette étape prend aussi **O(n)** : elle parcourt les données un nombre constant de fois, pas une fois par produit.

Le temps affiché dans l'application mesure la construction de l'index et le calcul du comparatif. Il n'inclut pas la lecture initiale et le nettoyage des fichiers, le calcul des moyennes historiques ni le temps d'affichage de l'interface. La valeur change selon l'ordinateur et l'environnement Python ; le nombre de millisecondes affiché n'est donc pas une constante attendue partout.

## Organisation du code : MVC

Le projet suit l'architecture **MVC** : Modèle, Vue, Contrôleur. On peut la comprendre comme une séparation des rôles.

| Partie | Son rôle dans ce projet | Fichiers principaux |
|---|---|---|
| **Modèle** | Représente les produits, les offres, les prix historiques et les résultats de comparaison. | `models/entities.py` |
| **Vue** | Affiche la fenêtre, le menu, les tableaux et les boutons PyQt6. | `views/main_window.py` |
| **Contrôleur** | Réagit aux boutons, lance le chargement et transmet les résultats à l'écran. | `controllers/main_controller.py` |
| **Services** | Contient la lecture, le nettoyage, le rapprochement, les calculs et l'écriture des résultats traités. | `services/data_loader.py`, `services/analysis_service.py`, `services/output_writer.py` |
| **Point de départ** | Crée l'application et ouvre sa fenêtre. | `main.py` |

Cette séparation évite de mélanger l'affichage des boutons avec les règles de calcul des prix.

## Dépendances

Les bibliothèques nécessaires sont listées dans `requirements.txt` :

- **PyQt6** crée l'interface de bureau ;
- **pandas** lit les fichiers CSV et exporte le comparatif ;
- **openpyxl** lit le classeur Excel.

La lecture du JSON utilise le module `json`, déjà fourni avec Python.

## Résumé de conformité à l'énoncé

| Élément demandé | Où le trouver dans l'application |
|---|---|
| Chargement CSV, JSON et Excel | Bouton **Lancer l'analyse** et compteur d'offres |
| Nettoyage et journal | Menu **Journal de nettoyage**, `donnees_nettoyees/` et `logs/` |
| Rapprochement au catalogue | Identifiants P01 à P30 et nombre d'articles à rapprocher |
| Prix, enseigne moins chère, écarts | Menu **Comparatif des prix** et export CSV |
| Nombre de victoires, écart moyen, top 3 | **Vue d'ensemble** |
| Coût du panier par enseigne et panier optimisé | Menu **Panier de rentrée** |
| Comparaison annuelle et Black Friday | Menu **Historique** |
| Complexité et mesure du temps | Carte de temps dans la vue d'ensemble et section ci-dessus |

## Fichiers du projet

```text
main.py
requirements.txt
README.md
.gitignore
models/
views/
controllers/
services/
donnees_nettoyees/       # offres normalisées et historique nettoyé (créés à l'analyse)
logs/                    # journal lisible et journal technique
Data/
exports/                 # comparatif exporté depuis l'application
```

Le dossier `exports/` accueille les comparatifs exportés. Le fichier `.gitignore` empêche notamment d'ajouter à Git l'environnement virtuel, les fichiers temporaires Python et le journal local.
>>>>>>> 9418a67 (Crée l'architecture MVC)
