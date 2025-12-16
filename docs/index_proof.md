# Preuve d'impact d'un index (Article.title)

Ce document illustre, au moyen de requêtes Cypher et de l'utilisation de `PROFILE`/`EXPLAIN`, l'amélioration attendue lors de l'ajout d'un index sur `:Article(title)`.

## 1) Requête sans index

Requête (recherche d'un film par titre) :

```
PROFILE
MATCH (a:Article)
WHERE a.title = 'Inception'
RETURN a
```

Comportement attendu sans index :
- le moteur doit examiner (scan) tous les nœuds `:Article` (node scan) et tester la condition `a.title = 'Inception'` pour chacun ; coûts proportionnels à la taille du corpus.

## 2) Création de l'index

```
CREATE INDEX article_title IF NOT EXISTS FOR (a:Article) ON (a.title)
```

Après création, l'index permet au moteur d'utiliser une recherche indexée plutôt qu'un node scan.

## 3) Même requête avec index

```
PROFILE
MATCH (a:Article)
WHERE a.title = 'Inception'
RETURN a
```

Comportement attendu avec index :
- l'opération utilise l'index pour localiser directement les nœuds candidats (index seek) ; le plan renvoyé par `PROFILE` montre l'usage de l'index et des compteurs d'`dbHits` plus faibles.

## 4) Interpretation (courte preuve)

- `PROFILE` affiche le plan d'exécution détaillé et le nombre de dbHits (accès disque/opérations internes). Une recherche indexée doit montrer significativement moins de `dbHits` et une étape `Index Seek` ou équivalente au lieu d'un `Node By Label Scan`.
- En pratique, pour un dataset large (10k+ films), le passage d'un node-scan à un index-seek réduit le coût de O(N) à O(log N) ou O(1) selon la structure d'index et la sélectivité, améliorant nettement la latence des requêtes.

---

Remarque : exécutez ces commandes dans Neo4j Browser ou via bolt (cypher-shell) pour observer les différences de plan sur vos données réelles.
