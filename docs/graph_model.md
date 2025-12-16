# Schéma du Knowledge Graph — Domaine : Films (Wikidata)

> Cette page documente le schéma Neo4j utilisé pour le dataset Films (Wikidata). Elle présente la modélisation (nœuds, relations, propriétés clés), une représentation diagrammatique (Mermaid et ASCII), des explications conceptuelles et une justification académique de l'utilisation d'une base de graphes.

---

## 1. Résumé du schéma

- Nœuds principaux :
  - `:Article` — représente un **Film**
  - `:Author` — représente un **Réalisateur (Director)**
  - `:Topic` — représente un **Genre**

- Relations :
  - `(:Author)-[:DIRECTED]->(:Article)`
  - `(:Article)-[:HAS_TOPIC]->(:Topic)`

- Propriétés clés :
  - `Article` : `wikidata_id` (string, UNIQUE), `title` (string), `year` (integer, optional)
  - `Author`  : `wikidata_id` (string, UNIQUE), `name` (string)
  - `Topic`   : `name` (string, UNIQUE)

> Remarque : la terminologie s'aligne avec le dataset Wikidata Films : Article = Film, Author = Director, Topic = Genre.

---

## 2. Diagrammes (texte)

### 2.1 Mermaid (à copier dans un rendu Mermaid)
```mermaid
graph LR
  Author[Author\n+ wikidata_id (UNIQUE)\n+ name] -->|DIRECTED| Article[Article\n+ wikidata_id (UNIQUE)\n+ title\n+ year (optional)]
  Article -->|HAS_TOPIC| Topic[Topic\n+ name (UNIQUE)]
```

### 2.2 ASCII
```
[Author {wikidata_id*, name}] -[:DIRECTED]-> [Article {wikidata_id*, title, year?}] -[:HAS_TOPIC]-> [Topic {name*}]
(* = propriété unique / clé)
```

### 2.3 Indications visuelles pour draw.io
- Placement : `Author` à gauche, `Article` au centre, `Topic` à droite (flux logique : Author → Article → Topic).
- Couleurs suggérées :
  - `Author` : bleu (#4A90E2)
  - `Article` : vert (#7ED321)
  - `Topic` : orange (#F5A623)
- Étiquettes : afficher le label (gras) et, en dessous, les propriétés clés (petit). Les relations doivent être des arêtes orientées étiquetées `DIRECTED` et `HAS_TOPIC`.

---

## 3. Rôle des types de nœuds et des relations

### 3.1 `Article` (Film)
- Rôle : unité de contenu principale représentant un film. Sert de cible pour la recherche et de base pour les recommandations et l'exploration thématique.
- Propriétés essentielles : `wikidata_id` (identifiant unique), `title`, `year` (optionnelle).

### 3.2 `Author` (Réalisateur)
- Rôle : entité créatrice (réalisateur) liée aux films qu'il a dirigés. Permet d'effectuer des analyses de contributions et de similarité par auteur.
- Propriétés essentielles : `wikidata_id`, `name`.

### 3.3 `Topic` (Genre)
- Rôle : classification thématique des films. Un film peut avoir plusieurs genres ; les genres permettent d'explorer des sous‑graphes par co‑occurrence.
- Propriété essentielle : `name`.

### 3.4 Justification des relations
- `DIRECTED` : capture la relation naturelle « a réalisé », essentielle pour analyser les contributions des réalisateurs et pour trouver des films similaires par auteur.
- `HAS_TOPIC` : associe films et genres ; sert à la découverte par genre et au calcul de co‑occurrence entre genres.

---

## 4. Requêtes graphiques — explication conceptuelle (haut niveau)

### 4.1 Recherche sémantique (films, réalisateurs, genres)
- Utiliser des indexes full‑text sur `Article.title`, `Author.name`, `Topic.name` pour permettre des recherches textuelles rapides.
- Pour une requête globale, effectuer une recherche full‑text sur chaque label concerné, puis agréger et scorer les résultats en combinant la similarité textuelle et des signaux graphiques (degré du nœud, nombre de relations, centralité).

### 4.2 Trouver des films liés (similarité)
- Signaux de similarité :
  - Partage de réalisateurs (poids élevé)
  - Partage de genres (poids moyen, pondéré par la rareté du genre)
  - Proximité temporelle (différence d'`year` — poids faible)
- Approche : agréger ces signaux via une traversée (trouver voisins à distance 1–2), calculer un score pondéré et retourner le top‑K.

### 4.3 Explorer un genre (sous‑graphe par co‑occurrence)
- Construire un graphe des genres où deux `Topic` sont reliés si elles co‑apparaissent dans des `Article`. L'arête peut être pondérée (nombre d'articles partagés).
- Utilisation : visualisation, détection de communautés de genres, ou découverte de genres connexes.

### 4.4 Récupérer les contributions d'un réalisateur
- Traverser `(:Author)-[:DIRECTED]->(:Article)` pour lister les films dirigés, agréger par année, et calculer des métriques (nombre de films, distribution temporelle, etc.).

---

## 5. Justification académique — pourquoi Neo4j / graph databases ?

- **Modélisation relationnelle naturelle** : le domaine filmographique est centré sur des relations (réalisateur→film, film→genre). Les graphes rendent ces relations premières et directement navigables.
- **Traversées efficaces** : les opérations de découverte et de similarité reposent sur l'exploration de voisinages et de motifs (ex. co‑occurrence) — tâches qui s'expriment naturellement et s'exécutent efficacement en base de graphes.
- **Co‑occurrence et raisonnement relationnel** : la similarité émergente (partage de réalisateurs, genres) est obtenue par des traversées et des agrégations de relations plutôt que par des jointures coûteuses.
- **Analyses structurelles** : centralité, communautés et pondération d'arêtes sont des signaux structurels exploitables pour améliorer le ranking et la découverte.
- **Extensibilité** : le modèle minimal proposé est robuste et s'étend facilement (ex. propriétés additionnelles, relations dérivées, index materialisés) sans compromettre la sémantique.

---

## 6. Recommandations d'implémentation et bonnes pratiques

- Définir des contraintes et indexes (`UNIQUE` sur `wikidata_id`/`name`) lors de l'initialisation de la base pour garantir l'intégrité et de bonnes performances.
- Créer un index full‑text multi‑label (Articles / Authors / Topics) pour la recherche globale.
- Pour la fonctionnalité « related films », privilégier une requête dynamique pour réactivité, et proposer en option une matérialisation périodique pour les volumes très importants.

---

## 7. Notes finales

- Ce document est strictement focalisé sur le schéma et la documentation associée au dataset Films (Wikidata). Il **n'inclut pas** d'éléments hors‑sujet (anciennes données, tags ou relations non spécifiées).

Si vous souhaitez, je peux également générer un fichier `draw.io` (XML) contenant le diagramme visuel conformément aux indications ci‑dessus.
