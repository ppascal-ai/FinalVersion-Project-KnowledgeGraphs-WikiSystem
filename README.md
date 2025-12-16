# Knowledge Graph API – Wikidata Film Explorer

**Projet AIDAMS 3A – Graph Databases & Knowledge Graphs**

Projet réalisé dans le cadre du cours **Graph Databases & Knowledge Graphs**.
L’objectif est de concevoir une **API REST de Knowledge Graph** basée sur **Neo4j** et **FastAPI**, permettant l’exploration avancée d’un graphe réel issu de **Wikidata** (films, auteurs, genres).

---

## 👥 Équipe

* **Paul Pascal** (Team Lead)
* Andrea Surace Gomez
* Toscane Cesbron Darnaud

---

## 1. Objectif du projet

Le but de ce projet est de construire une **API de graphes de connaissances** permettant :

* la **modélisation d’un dataset réel** sous forme de graphe,
* l’**exploration relationnelle** (traversals multi-sauts),
* l’**analyse des contributions d’auteurs**,
* la **recherche de contenu par thème**,
* la **recommandation et la proximité sémantique** via des chemins dans le graphe,
* l’exposition de **requêtes Cypher avancées** via une API FastAPI documentée.

Le projet met en pratique :

* la modélisation Neo4j,
* l’optimisation de requêtes,
* l’ingestion de données externes,
* les tests, le linting et le déploiement Docker.

---

## 2. Dataset

### Source

Le projet utilise un **dataset réel issu de Wikidata**, récupéré via des requêtes **SPARQL**.

Les données portent sur :

* des **films**,
* leurs **réalisateurs / auteurs**,
* leurs **genres cinématographiques**.

Les données sont publiques et maintenues par la communauté Wikidata.

### Justification du choix

Ce dataset est particulièrement adapté à un **graph database** car :

* les relations sont centrales (films ↔ auteurs ↔ genres),
* les parcours multi-niveaux sont naturels (ex. : auteurs reliés par des genres communs),
* il permet d’illustrer des **cas d’usage concrets** : recommandations, similarités, analyses de contributions.

---

## 3. Architecture du projet

```
.
├── app
│   ├── main.py
│   ├── security.py
│   ├── database
│   │   └── neo4j.py
│   ├── models
│   │   └── schemas.py
│   └── routers
│       ├── search.py
│       ├── articles.py
│       ├── topics.py
│       └── authors.py
├── scripts
│   ├── generate_diagrams.py
│   ├── import_wikidata.py
│   └── seed_data.py
├── docs
│   ├── graph_model.md
│   ├── index_proof.md
│   └── diagrams
│       ├── architecture.drawio
│       ├── architecture.png
│       ├── neo4j_schema.drawio
│       └── neo4j_schema.png
├── tests
│   ├── test_health.py
│   ├── test_search.py
│   ├── test_articles.py
│   ├── test_authors.py
│   ├── test_topics.py
│   ├── test_cyper_queries.py
│   └── test_graph_queries.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── Makefile
├── demo.ipynb
├── README.md
└── .env.example
```

---

## 4. Diagrams

### System Architecture

!(docs/diagrams/architecture.png)

* FastAPI (port 8000)
* Neo4j (7474 / 7687)
* Scripts d’ingestion et de seed
* Tests automatisés

---

### Neo4j Graph Schema

!(docs/diagrams/neo4j_schema.png)

---

## 5. Modèle de graphe Neo4j

### Nœuds

| Label       | Description                     |
| ----------- | ------------------------------- |
| **Article** | Film (wikidata_id, title, year) |
| **Author**  | Réalisateur / auteur            |
| **Topic**   | Genre cinématographique         |

---

### Relations

| Relation                               | Description                   |
| -------------------------------------- | ----------------------------- |
| `(:Author)-[:DIRECTED]->(:Article)`    | Un auteur a réalisé un film   |
| `(:Article)-[:HAS_TOPIC]->(:Topic)`    | Un film appartient à un genre |
| `(:Topic)-[:CO_OCCURS_WITH]->(:Topic)` | Genres apparaissant ensemble  |

---

### Contraintes & Index

Créés automatiquement lors du seed :

* Contraintes d’unicité :

  * `Article.wikidata_id`
  * `Author.wikidata_id`
  * `Topic.name`
* Index :

  * `Article.title`
  * `Article.year`
  * `Author.name`

---

## 6. Modeling Rationale

Le modèle est volontairement **simple mais expressif**.

* **Article** représente le contenu central.
* **Author** permet l’analyse des contributions et des proximités entre réalisateurs.
* **Topic** sert de pivot sémantique pour la navigation et la similarité.

La relation **CO_OCCURS_WITH** enrichit le graphe en capturant des co-occurrences réelles entre genres, ce qui permet :

* des recommandations,
* des parcours indirects,
* des analyses de similarité.

Neo4j est particulièrement adapté à ce modèle car il permet :

* des traversals multi-sauts efficaces,
* l’exécution de requêtes analytiques complexes sans jointures coûteuses,
* une évolution simple du schéma.

---

## 7. Data Ingestion & Seed

### Import Wikidata

```bash
make import-wikidata
```

* Requêtes SPARQL vers Wikidata
* Transformation et insertion dans Neo4j
* Pas de wipe par défaut

### Seed

```bash
make seed
```

* Création des contraintes et index
* Construction des relations `CO_OCCURS_WITH`
* Vérification des volumes insérés

---

## 8. API – FastAPI

Documentation interactive :
👉 **[http://localhost:8000/docs](http://localhost:8000/docs)**

*(Ajouter captures Swagger ici)*

### Endpoints principaux

| Endpoint                          | Description                      |
| --------------------------------- | -------------------------------- |
| `/health`                         | Healthcheck                      |
| `/api/search`                     | Recherche de films               |
| `/api/articles/{id}/related`      | Films liés (protégé par API key) |
| `/api/topics/{topic}/graph`       | Sous-graphe autour d’un genre    |
| `/api/authors/{id}/contributions` | Contributions d’un auteur        |

---

## 9. Requêtes Cypher avancées

Le projet implémente :

* **shortestPath** (proximité entre auteurs),
* OPTIONAL MATCH,
* agrégations (`count`, `ORDER BY`),
* requêtes analytiques,
* **EXPLAIN / PROFILE** pour l’optimisation.

Les indexes sont effectivement utilisés (vérifié via EXPLAIN).

---

## 10. Notebook de démonstration

Un notebook `demo.ipynb` est fourni pour :

* explorer le graphe,
* exécuter des requêtes Cypher avancées,
* analyser les performances,
* illustrer les cas d’usage métier.

---

## 11. Tests & Qualité

* Tests unitaires et d’intégration (`pytest`)
* Linting avec **pylint**
* Score pylint : **9.7 / 10**
* `make test`, `make lint`, `make help` fonctionnels

---

## 12. Docker

Image publique disponible sur Docker Hub :

👉 [https://hub.docker.com/repository/docker/ppascal92/graph-api/general](https://hub.docker.com/repository/docker/ppascal92/graph-api/general)

Lancement rapide :

```bash
make up
```

---

## 13. Conclusion

Ce projet démontre :

* une **modélisation pertinente d’un graphe réel**,
* une **API FastAPI propre et documentée**,
* l’utilisation de **Cypher avancé**,
* une **architecture Docker reproductible**,
* un **code testé, linté et maintenable**.
