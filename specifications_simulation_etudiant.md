# Spécifications d'implémentation
## Simulation d'un étudiant autonome vivant seul pendant une année universitaire

**Version** : 1.0
**Date** : 9 juillet 2026
**Statut** : Prêt pour implémentation (MVP)

---

## 1. Contexte et objectifs

Le projet consiste à simuler, sur une année universitaire, le comportement d'un unique agent autonome — un étudiant vivant seul — confronté à des besoins concurrents (finances, santé, académique, social), un budget limité et des événements imprévus.

Objectif pédagogique : poser, sur un seul agent, l'ensemble des briques architecturales (BDI, fonction d'utilité, planification HTN, émotions, événements stochastiques) qui seront réutilisées et étendues dans le mémoire, avant de passer à un système multi-agents.

**Critère de réussite du MVP** : une simulation exécutable de bout en bout sur une année académique, produisant une trajectoire cohérente (l'agent mange, dort, étudie, travaille, réagit aux événements) et un jeu d'indicateurs exploitables (courbes de santé/stress/argent, taux de réussite aux examens, journal des décisions).

### Hors périmètre (MVP)

- Multi-agents et interactions sociales (prévu en extension via `networkx`).
- Interface graphique — sorties en console + fichiers CSV/PNG uniquement.
- Apprentissage par renforcement profond ou LLM dans la boucle de décision.
- Persistance en base de données (les résultats sont sérialisés en fichiers plats).

---

## 2. Vue d'ensemble architecturale

Arborescence du projet et responsabilité de chaque module :

| Fichier | Rôle |
|---|---|
| `core/environment.py` | État du monde partagé : calendrier universitaire, prix courants, météo simple, référentiel des lieux (logement, université, travail, commerces). Expose une API de lecture pour les perceptions de l'agent. |
| `core/scheduler.py` | Orchestre l'ordre d'exécution des cycles : appelle le moteur d'événements, puis le cycle cognitif de l'agent, puis la collecte de stats, à chaque pas de temps. |
| `core/clock.py` | Horloge de simulation : pas de temps, date/heure courante, conversion jour universitaire ↔ jour calendaire, détection des périodes (cours, examens, vacances). |
| `agents/student.py` | Classe `Student` : point d'entrée de l'agent, assemble beliefs/desires/intentions/mémoire/émotions et exécute le cycle cognitif. |
| `agents/planner.py` | Planificateur HTN : décompose les désirs actifs en intentions concrètes (séquences d'actions). |
| `agents/beliefs.py` | Structure et mise à jour des croyances (état perçu du monde et de soi). |
| `agents/desires.py` | Génération et priorisation des désirs à partir des besoins/motivations. |
| `agents/intentions.py` | Pile d'intentions courantes, gestion de l'engagement et de l'abandon de plan. |
| `cognition/memory.py` | Mémoire court terme (événements récents) et long terme (statistiques d'expérience : quelles actions ont bien/mal fonctionné). |
| `cognition/emotion.py` | Modèle émotionnel (stress, anxiété, satisfaction, moral) et ses règles de mise à jour/décroissance. |
| `cognition/motivation.py` | Traduit l'état des besoins (faim, fatigue, finances, académique, social) en intensité de désirs. |
| `cognition/decision.py` | Sélectionne l'action à exécuter parmi les options du plan courant, à partir de l'utilité. |
| `cognition/utility.py` | Calcule `U(a)` pour une action donnée à partir des critères pondérés. |
| `actions/work.py`, `eat.py`, `study.py`, `sleep.py`, `leisure.py` | Implémentation de chaque action primitive : préconditions, effets, durée, coût. |
| `events/illness.py`, `exam.py`, `rent.py`, `inflation.py` | Générateurs d'événements stochastiques ou calendaires qui modifient l'environnement/les croyances. |
| `models/economy.py` | Revenus, dépenses, budget, inflation. |
| `models/nta.py` | Modèle Besoins–Seuils–Alertes (*Needs–Thresholds–Alerts*) : dynamique des besoins physiologiques/psychologiques et déclenchement d'alertes quand un seuil critique est franchi. |
| `statistics/indicators.py` | Calcul des indicateurs agrégés (KPIs) à partir du journal de simulation. |
| `statistics/plots.py` | Génération des graphiques (Matplotlib/Plotly). |
| `main.py` | Point d'entrée : charge la config, instancie l'environnement et l'agent, lance le scheduler, exporte les résultats. |

---

## 3. Modèle d'agent : Utility-Based Agent à architecture BDI

### 3.1 Beliefs (croyances)

Représentation interne et subjective de l'état du monde et de soi. Implémentée comme un modèle Pydantic (`agents/beliefs.py`), mise à jour à chaque cycle par perception (lecture de `environment.py`) — jamais modifiée directement par les actions.

| Champ | Type | Exemple |
|---|---|---|
| `money` | `float` (FCFA) | 75000 |
| `days_to_next_exam` | `int` | 10 |
| `fatigue` | `float` [0,100] | 62 |
| `hunger` | `float` [0,100] | 40 |
| `stress` | `float` [0,100] | 55 |
| `health` | `float` [0,100] | 80 |
| `academic_progress` | `float` [0,100] par matière | {"Maths": 45} |
| `calendar_events` | `list[Event]` | examens, cours, échéances loyer |
| `job_status` | `enum` {employed, unemployed} | employed |
| `last_meal_hours_ago` | `int` | 6 |
| `sleep_debt` | `float` (heures) | 3.5 |

### 3.2 Desires (désirs)

Objectifs que l'agent souhaite atteindre, générés par `cognition/motivation.py` à partir des beliefs. Chaque désir porte une **intensité** (0–1) recalculée chaque cycle.

| Désir | Déclencheur principal |
|---|---|
| Réussir l'examen | `days_to_next_exam` faible et `academic_progress` insuffisant |
| Payer le loyer | échéance `rent` proche dans `calendar_events` |
| Rester en bonne santé | `health` bas ou `fatigue`/`stress` élevés |
| Se nourrir | `hunger` au-delà d'un seuil |
| Se reposer | `sleep_debt` élevé |
| Se détendre | `stress` élevé et pas d'urgence académique/financière |

### 3.3 Intentions

Séquence d'actions engagée, produite par `agents/planner.py` (HTN) à partir du désir dominant, stockée dans `agents/intentions.py` sous forme de pile. Une intention est abandonnée et une replanification est déclenchée si :
- un événement modifie significativement les croyances (ex. maladie, examen surprise) ;
- une précondition d'action du plan n'est plus satisfaite (ex. argent insuffisant) ;
- un désir plus urgent dépasse un seuil de priorité configurable.

---

## 4. Cycle cognitif

Pas de temps par défaut : **1 heure simulée**. Chaque cycle exécute la séquence suivante (implémentée dans `agents/student.py`, orchestrée par `core/scheduler.py`) :

```
1. Perception          : lecture de environment.py (heure, prix, calendrier, événements actifs)
2. Mise à jour beliefs  : agents/beliefs.py
3. Mise à jour émotions : cognition/emotion.py (décroissance + réaction aux beliefs/événements)
4. Génération désirs    : cognition/motivation.py -> agents/desires.py
5. Planification        : agents/planner.py (HTN, seulement si pas de plan actif ou replanification requise)
6. Choix de l'action    : cognition/decision.py + cognition/utility.py, sur les options du plan courant
7. Exécution            : actions/*.py -> effets appliqués aux beliefs et à environment.py
8. Apprentissage simple : cognition/memory.py (mise à jour des statistiques succès/échec par type d'action)
9. Collecte statistiques: statistics/indicators.py (journalisation de l'état + décision du cycle)
```

Le scheduler avance l'horloge (`core/clock.py`) d'un pas, déclenche les événements dus (`events/*.py`), puis appelle ce cycle pour l'agent.

---

## 5. Planification (HTN simplifié)

### 5.1 Arbre de décomposition

```
Objectif racine : Obtenir le diplôme
├── Assister aux cours
│     → action primitive : study.attend_course
├── Étudier
│     → tâches composées : réviser_matière(x) → séquence d'actions study.review
├── Dormir suffisamment
│     → action primitive : sleep.sleep(duration)
├── Réduire le stress
│     → tâches composées : leisure.rest | leisure.socialize (selon budget/temps disponible)
└── Payer les frais universitaires / le loyer
      → tâches composées : work.shift(s) puis eat.budget_meal si besoin d'économiser
```

### 5.2 Règles de décomposition

Chaque sous-objectif possède une ou plusieurs **méthodes** de décomposition en actions primitives, sélectionnées selon le contexte (beliefs courants). Exemple pour *Payer le loyer* :

- Si `money >= rent_due` → méthode "payer directement" (1 action).
- Si `money < rent_due` et `days_to_rent_due > 3` → méthode "travailler puis payer" (n × `work.shift` jusqu'à solvabilité, puis paiement).
- Si `money < rent_due` et `days_to_rent_due <= 1` → méthode "solliciter aide familiale" (déclenche l'événement `rent.request_family_help` avec probabilité de succès).

Le planificateur ne recalcule un plan que lorsque : aucun plan actif n'existe, le plan courant est épuisé, ou une condition de replanification (section 3.3) est levée.

---

## 6. Décision et fonction d'utilité

Pour chaque action candidate `a` issue du plan courant (ou, en l'absence de plan, du catalogue d'actions disponibles compte tenu des préconditions), on calcule :

```
U(a) = Σ_i  w_i · f_i(a)
```

où chaque `f_i(a)` est normalisée dans [0, 1] et `Σ w_i = 1`.

| Critère `f_i` | Ce qu'il mesure | Poids par défaut `w_i` |
|---|---|---|
| Progression académique | gain estimé sur `academic_progress` | 0.25 |
| Coût financier | coût normalisé de l'action / `money` disponible (pénalise) | 0.20 |
| Fatigue | impact sur `fatigue`/`sleep_debt` (pénalise si déjà élevé) | 0.15 |
| Stress | impact sur `stress` (pénalise si déjà élevé) | 0.15 |
| Faim | réduction de `hunger` si applicable | 0.15 |
| Satisfaction personnelle | gain de moral/plaisir (issu du modèle d'émotion) | 0.10 |

Règles complémentaires :

- **Contraintes dures** : une action est exclue des candidats si ses préconditions ne sont pas satisfaites (ex. `work.shift` nécessite `job_status == employed` et `fatigue < seuil_max`).
- **Bruit d'exploration** : un terme aléatoire faible (ε, configurable, ex. 0.02) est ajouté à `U(a)` pour éviter un comportement strictement déterministe et représenter la variabilité humaine.
- **Pondération dynamique** : les poids `w_i` peuvent être ajustés par `cognition/emotion.py` (ex. un stress élevé augmente temporairement `w_stress`) — mécanisme optionnel, activable par configuration.
- L'agent exécute l'action de `U(a)` maximale parmi les candidates.

---

## 7. Mémoire et apprentissage simple

`cognition/memory.py` maintient :

- **Mémoire court terme** : fenêtre glissante des N derniers cycles (événements, actions, beliefs) — utilisée pour détecter des tendances (ex. plusieurs nuits de sommeil insuffisant consécutives).
- **Mémoire long terme** : compteurs succès/échec par type d'action (ex. taux de réussite des examens après une stratégie de révision intensive vs. répartie), utilisés pour ajuster légèrement les poids `w_i` ou les seuils de décision au fil de la simulation (apprentissage par renforcement simple, type moyenne mobile — pas de deep learning).

---

## 8. Modèle émotionnel

`cognition/emotion.py` maintient au minimum deux dimensions continues [0,100] :

- **Stress** : augmente avec l'imminence des examens, les difficultés financières, le manque de sommeil ; diminue avec le repos, les loisirs, l'atteinte d'objectifs.
- **Moral / satisfaction** : augmente avec la réussite d'actions (repas pris, examen réussi, loisir), diminue avec les échecs et la privation prolongée.

Chaque émotion suit une règle de mise à jour de la forme `E_t = clamp(E_{t-1} + Δ(beliefs, événements) − decay, 0, 100)`, avec un terme de décroissance naturelle vers un niveau de base (`baseline`) en l'absence de stimulus. Les émotions influencent la fonction d'utilité (section 6) et peuvent moduler la génération des désirs (ex. un stress très élevé augmente l'intensité du désir "se détendre").

---

## 9. Modèle de besoins (NTA — Needs / Thresholds / Alerts)

`models/nta.py` formalise la dynamique des besoins fondamentaux (faim, sommeil, hygiène/santé, lien social, finances) :

- Chaque besoin a une valeur courante, un taux de dégradation naturel par cycle (ex. `hunger += 2/heure`), et un ou plusieurs **seuils** (confort, alerte, critique).
- Le franchissement d'un seuil d'alerte déclenche une **alerte** consommée par `cognition/motivation.py` pour générer/renforcer un désir correspondant.
- Le franchissement du seuil critique a un effet direct sur `health` (pénalité) et peut déclencher un événement (ex. `events/illness.py`).

---

## 10. Catalogue des actions primitives

| Action (fichier) | Préconditions | Effets principaux | Durée |
|---|---|---|---|
| `work.shift` | `job_status == employed`, `fatigue < seuil` | `+money`, `+fatigue`, `+stress` léger | 4 h |
| `eat.budget_meal` / `eat.normal_meal` | `money >= coût du repas` | `-hunger`, `-money`, `+health` léger | 0.5–1 h |
| `study.attend_course` | cours programmé au créneau | `+academic_progress` léger, `+fatigue` léger | 2–3 h |
| `study.review` | `energy`/`fatigue` sous seuil | `+academic_progress`, `+fatigue`, `+stress` (si intensif) | 1–3 h |
| `sleep.sleep` | disponibilité du créneau nocturne | `-fatigue`, `-sleep_debt`, `+health` léger | 6–8 h |
| `leisure.rest` / `leisure.socialize` | `money` suffisant si sortie payante | `-stress`, `+moral` | 1–3 h |

Chaque module d'action expose une interface commune : `preconditions(beliefs) -> bool`, `apply(beliefs, environment) -> beliefs_delta`, `duration`, `cost`.

---

## 11. Moteur d'événements

| Événement (fichier) | Type de déclenchement | Effet |
|---|---|---|
| `illness.py` | probabiliste, probabilité croissante avec `fatigue`/`stress` élevés (loi issue de `scipy.stats`) | `-health`, `+fatigue`, interruption temporaire des actions académiques/travail |
| `exam.py` | calendaire (planifié) + variante "examen surprise" (probabiliste, faible probabilité) | crée/avance une échéance dans `calendar_events`, force replanification |
| `rent.py` | calendaire (mensuel) | échéance de paiement ; en cas de non-paiement, pénalité (stress, risque d'expulsion simulé) |
| `inflation.py` | périodique ou probabiliste | augmente le coût des repas/loyer dans `models/economy.py` |
| (bonus) perte d'emploi étudiant | probabiliste, conditionnée par contexte économique | `job_status = unemployed`, `+stress` |
| (bonus) aide familiale exceptionnelle | probabiliste | `+money`, `-stress` |

Chaque événement, une fois déclenché par `core/scheduler.py`, modifie `environment.py` et/ou force une mise à jour des `beliefs` de l'agent au cycle suivant, ce qui peut invalider le plan courant et déclencher une replanification (section 5.2).

---

## 12. Modèle économique

`models/economy.py` gère :
- Revenus : salaire du job étudiant (si `employed`), aide familiale ponctuelle.
- Dépenses : loyer (mensuel), nourriture (par repas), imprévus.
- Inflation : coefficient appliqué périodiquement aux prix de référence, piloté par `events/inflation.py`.

---

## 13. Statistiques et indicateurs

`statistics/indicators.py` calcule, à partir du journal de simulation (un enregistrement par cycle exporté en `pandas.DataFrame`) :

- Trajectoires temporelles : argent, santé, stress, fatigue, moral, progression académique par matière.
- Taux de réussite aux examens, nombre de jours en situation financière critique (`money < 0` ou proche), nombre d'épisodes de maladie.
- Répartition du temps par catégorie d'action (travail / étude / sommeil / loisir / autre).
- Corrélations simples (ex. stress vs. réussite académique) à titre exploratoire.

`statistics/plots.py` génère les visualisations correspondantes (Matplotlib pour les courbes statiques, Plotly en option pour l'exploration interactive) et les exporte en PNG/HTML.

---

## 14. Configuration et validation (Pydantic)

Deux schémas Pydantic pilotent la simulation, définis en configuration (`config.yaml` ou équivalent) et validés au démarrage par `main.py` :

- **`AgentProfile`** : état initial des beliefs (argent de départ, santé, etc.), poids `w_i` de la fonction d'utilité, seuils NTA, paramètres émotionnels (baseline, taux de décroissance).
- **`SimulationConfig`** : durée de la simulation (par défaut ~270 jours, année académique septembre–juin), pas de temps, graine aléatoire (`seed`) pour la reproductibilité, paramètres des lois statistiques des événements, chemins de sortie.

---

## 15. Dépendances techniques

| Bibliothèque | Usage |
|---|---|
| Mesa | infrastructure de simulation (agent, scheduler, environnement) |
| NumPy | calculs numériques, distributions |
| Pandas | journal de simulation, agrégation des résultats |
| SciPy | lois statistiques pour la génération des événements aléatoires |
| NetworkX | réservé aux extensions multi-agents/réseau social (hors MVP) |
| Matplotlib / Plotly | visualisation des indicateurs |
| Pydantic | validation des profils d'agent et des paramètres de simulation |

Explicitement exclus du MVP : LLM et frameworks cognitifs lourds (ACT-R, SOAR).

---

## 16. Plan de développement proposé

| Phase | Contenu | Sortie attendue |
|---|---|---|
| 1. Socle | `core/*`, `models/nta.py`, `models/economy.py`, beliefs statiques | environnement + horloge fonctionnels, sans agent actif |
| 2. Agent réactif | `actions/*`, `cognition/utility.py`, `cognition/decision.py` sans planification (choix myope à chaque cycle) | l'agent choisit une action sensée à chaque heure |
| 3. BDI complet | `agents/beliefs.py`, `desires.py`, `intentions.py`, `agents/planner.py` (HTN) | plans multi-actions, replanification |
| 4. Émotion et mémoire | `cognition/emotion.py`, `cognition/memory.py` | pondération dynamique, apprentissage simple |
| 5. Événements | `events/*.py` | perturbations et replanification forcée |
| 6. Statistiques | `statistics/*.py`, `main.py` complet | rapport de simulation (CSV + graphiques) |
| 7. Calibrage | ajustement des poids/seuils par défaut | trajectoires plausibles sur une année complète |

---

## 17. Critères d'acceptation

- La simulation s'exécute de bout en bout sur une année académique sans erreur, avec une graine fixée (reproductibilité).
- À chaque cycle, une action et une seule est exécutée, choisie parmi des candidates dont les préconditions sont satisfaites.
- Les beliefs restent dans leurs bornes définies (ex. `[0,100]`, `money` peut être négatif pour représenter une dette, à définir explicitement en config).
- Au moins un événement de chaque type (`illness`, `exam`, `rent`, `inflation`) se produit et est visible dans le journal de décisions.
- Les indicateurs de `statistics/indicators.py` sont calculables sans erreur sur le journal produit, et les graphiques de `statistics/plots.py` s'exportent correctement.
- Un test de non-régression simple : deux exécutions avec la même graine produisent un journal identique.

---

## 18. Limites connues et extensions futures

- Un seul agent : aucune interaction sociale modélisée dans le MVP (réservé à `NetworkX` en extension).
- Fonction d'utilité linéaire pondérée : ne capture pas d'interactions non linéaires entre critères (ex. compromis santé/argent en situation extrême) ; envisageable en V2.
- Apprentissage limité à des statistiques simples (pas de RL formel) — cohérent avec l'objectif pédagogique du projet.
