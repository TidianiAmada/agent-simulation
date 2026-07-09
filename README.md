# Simulation d'un étudiant autonome — journal d'expérience

Ce document rend compte de l'expérience de référence (graine 42, profil par
défaut) exécutée avec le simulateur : un agent utility-based à architecture
BDI (beliefs / desires / intentions), planification HTN, modèle émotionnel
et besoins physiologiques (NTA), confronté à une année universitaire
(septembre 2025 → mai 2026) sous contrainte budgétaire et événements
imprévus. Pour l'installation et l'usage général de l'outil, voir la section
[Reproduire l'expérience](#reproduire-lexpérience) en fin de document ; pour
le cahier des charges complet, voir
[`specifications_simulation_etudiant.md`](specifications_simulation_etudiant.md).

## Objectif

Vérifier qu'un unique agent, doté des briques architecturales prévues
(croyances mises à jour par perception, désirs pondérés par les besoins et
les émotions, planification HTN, décision par fonction d'utilité,
apprentissage simple, événements stochastiques), produit sur une année
complète une trajectoire *cohérente* — l'agent mange, dort, étudie, travaille
et réagit aux imprévus — plutôt qu'un comportement erratique ou dégénéré.
C'est le critère de réussite du MVP (section 1 de la spécification), avant
extension à un système multi-agents.

## Protocole expérimental

| Paramètre | Valeur |
|---|---|
| Période simulée | 1<sup>er</sup> septembre 2025 → 29 mai 2026 (270 jours, ~2888 cycles de décision) |
| Graine (`seed`) | 42 |
| Argent initial | 75 000 FCFA |
| Santé / fatigue / faim / stress initiaux | 80 / 25 / 25 / 30 (sur 100) |
| Matières | Mathématiques, Algorithmique, Anglais |
| Loyer initial | 45 000 FCFA/mois (indexé sur l'inflation) |
| Poids de la fonction d'utilité | académique 0.25 · financier 0.20 · fatigue 0.15 · stress 0.15 · faim 0.15 · satisfaction 0.10 |
| Pondération dynamique du stress | activée (le poids du stress augmente temporairement au-delà de 60/80 de stress) |
| Bruit d'exploration ε | 0.02 |

Configuration complète : [`config/default.yaml`](config/default.yaml) ;
schémas et valeurs par défaut : [`config/schema.py`](config/schema.py).

## Résultats

### Vue d'ensemble (état final)

| Indicateur | Valeur |
|---|---|
| Argent final | 78 853 FCFA (minimum observé : 190 FCFA) |
| Jours en détresse financière (argent < 0) | 0 |
| Santé finale | 100 / 100 |
| Moral final | 65 / 100 |
| Stress moyen sur l'année | 18.7 / 100 |
| Fatigue moyenne sur l'année | 55.3 / 100 |
| Progression académique finale | Mathématiques 100 · Algorithmique 100 · Anglais 100 (sur 100) |
| Taux de réussite aux examens | 8 / 8 (100 %) |
| Épisodes de maladie | 3 |
| Corrélation stress ↔ progression académique | −0.067 (quasi nulle) |

### Trajectoire financière

L'agent reste solvable sur l'ensemble de l'année : le minimum observé
(190 FCFA) survient juste avant une paie, jamais en dette. Neuf échéances de
loyer sont honorées (de 45 000 à 47 493 FCFA, sous l'effet de l'inflation
cumulée), neuf ajustements d'inflation surviennent (environ un tous les 30
jours, de +0 % à +1.8 %), et une aide familiale spontanée de 13 367 FCFA est
reçue en mars. Le désir *payer le loyer* pousse l'agent à multiplier les
services de travail (`work.shift`) à l'approche de chaque échéance plutôt que
d'attendre — la méthode HTN « travailler puis payer » (section 5.2 du cahier
des charges) est bien celle qui domine sur cette expérience ; la méthode de
secours (solliciter la famille) n'a jamais été nécessaire dans ce run.

### Bien-être et santé

Stress et fatigue oscillent en dents de scie (le stress reste presque
toujours sous 40, la fatigue entre 20 et 90), signature attendue d'un cycle
répété tension → repos plutôt que d'une dérive monotone. La santé, partie de
80, remonte rapidement à ~100 et s'y maintient malgré trois épisodes de
maladie (décembre ×2, mai) — chacun de 28 à 47 h de convalescence — qui
créent des creux visibles mais temporaires sur la courbe. Le moral oscille
autour de 65-70 avec des pics après les réussites aux examens.

### Résultats académiques

| Matière | Date | Score | Résultat |
|---|---|---|---|
| Mathématiques | 2025-11-23 | 92.2 | Réussi |
| Mathématiques | 2025-12-29 | 92.5 | Réussi |
| Algorithmique | 2025-12-30 | 94.2 | Réussi |
| Anglais | 2025-12-31 | 99.1 | Réussi |
| Anglais | 2026-04-06 | 97.2 | Réussi |
| Mathématiques | 2026-05-22 | 89.5 | Réussi |
| Algorithmique | 2026-05-23 | 100.0 | Réussi |
| Anglais | 2026-05-24 | 96.1 | Réussi |

Les trois matières atteignent 100/100 de progression avant la fin de
l'année et les 8 examens (dont 2 examens surprises, en novembre et avril)
sont tous réussis. Le désir *réussir l'examen* domine largement en début de
semestre (cf. journal des décisions), avant de céder la place à *rester en
bonne santé* et *se détendre* une fois la progression suffisante.

### Répartition du temps (cumulée sur l'année)

| Catégorie | Heures | Part |
|---|---|---|
| Loisir | 2262 h | 35 % |
| Sommeil | 1632 h | 25 % |
| Travail | 1212 h | 19 % |
| Étude | 782 h | 12 % |
| Autre (repas, etc.) | 598 h | 9 % |

### Journal des événements (extraits)

```
Jour   4  Loyer payé (45 000)
Jour  82  Examen surprise annoncé : Mathématiques dans 2 jour(s)
Jour  83  Examen de Mathématiques réussi (score 92.2)
Jour  91  Maladie (sévérité 0.46, 28h de convalescence)
Jour 107  Maladie (sévérité 0.54, 43h de convalescence)
Jour 186  Aide familiale exceptionnelle reçue (+13 367)
Jour 251  Maladie (sévérité 0.68, 47h de convalescence)
Jour 270  Inflation : +1.8% sur les prix de référence
```

Journal complet : `output/events.csv`. Les quatre types d'événements requis
par le critère d'acceptation (maladie, examen, loyer, inflation) se
produisent tous au moins une fois — plus deux événements bonus (examen
surprise, aide familiale) ; la perte d'emploi (bonus, probabilité très
faible) ne s'est pas déclenchée sur cette graine.

## Discussion

- **Trajectoire cohérente** : le critère de réussite du MVP est atteint —
  l'agent alterne travail, étude, sommeil et loisirs de façon plausible, et
  réagit aux événements (replanification après maladie/examen surprise,
  intensification du travail avant le loyer).
- **Agent peut-être trop performant** : réussite à 100 % des examens, santé
  qui plafonne à 100, argent jamais négatif — un profil d'agent presque
  optimal plutôt qu'un profil « en difficulté ». Cela suggère une marge de
  calibrage (section 16.7 de la spécification) : durcir les seuils NTA,
  réduire le salaire ou augmenter le loyer, ou élever le coût cognitif de
  l'étude, pour obtenir des trajectoires plus tendues et des échecs
  occasionnels — utile pour étudier des compromis santé/argent plus
  marqués une fois en système multi-agents.
- **Corrélation stress/académique quasi nulle (−0.067)** sur ce run : à
  calibrage égal, le stress ne semble pas pénaliser la progression
  académique de façon significative ici — à confirmer sur plusieurs graines
  avant d'en tirer une conclusion structurelle.
- **Reproductibilité** : `tests/test_reproducibility.py` vérifie que deux
  exécutions à graine identique produisent un journal strictement identique,
  et qu'une graine différente change effectivement la trajectoire.

### Limites connues

Un seul agent (pas d'interaction sociale — réservé à `networkx` en
extension) ; fonction d'utilité linéaire pondérée (ne capture pas les
compromis non linéaires en situation extrême) ; apprentissage limité à des
statistiques simples (moyenne mobile succès/échec, pas de RL formel) ; ces
choix sont volontaires pour ce MVP à un agent (voir section 18 de la
spécification).

## Explorer la trajectoire

Un tableau de bord interactif rejoue cette expérience jour par jour (lecture
automatique, scrubbing, journal des événements, examens) :

```bash
python webapp/app.py     # puis ouvrir http://127.0.0.1:5000
```

Il permet aussi de relancer une nouvelle expérience (graine, durée) depuis le
navigateur pour comparer plusieurs trajectoires sans relancer la CLI.

## Reproduire l'expérience

```bash
python -m venv .venv
.venv/Scripts/activate        # Windows (PowerShell : .venv\Scripts\Activate.ps1)
# source .venv/bin/activate    # macOS / Linux
pip install -r requirements.txt

python main.py --config config/default.yaml
```

Exporte dans `output/` : `journal.csv` (un enregistrement par cycle : croyances,
action choisie, désir dominant, utilité), `events.csv`, `exam_results.csv`,
`indicators.json`, et les graphiques `trajectories.png`, `academic_progress.png`,
`time_allocation.png`, `exam_results.png`. Modifier `config/default.yaml`
(graine, durée, profil de l'agent, poids d'utilité, seuils NTA…) pour rejouer
une variante ; `config/schema.py` documente l'ensemble des paramètres.

Pour produire un tableau de bord HTML autonome (sans serveur) à partir du
dernier résultat exporté :

```bash
python dashboard/build_dashboard.py    # écrit dashboard/simulation_dashboard.html
```

Pour vérifier la reproductibilité et les critères d'acceptation :

```bash
pytest
```

### Structure du projet

```
config/       Schémas Pydantic (AgentProfile, SimulationConfig) + config/default.yaml
core/         Horloge, environnement (calendrier/prix/météo), scheduler
agents/       Beliefs, desires, intentions, planificateur HTN, classe Student
cognition/    Émotions, mémoire, motivation, fonction d'utilité, décision
actions/      Actions primitives (travailler, manger, étudier, dormir, loisirs, aide familiale)
events/       Générateurs d'événements (maladie, examens, loyer, inflation, perte d'emploi, aide familiale)
models/       Modèle de besoins NTA, modèle économique
statistics/   Indicateurs agrégés, graphiques Matplotlib, agrégation pour le tableau de bord
main.py       Point d'entrée CLI
webapp/       Application Flask (API + interface interactive)
dashboard/    Générateur du tableau de bord statique autonome
tests/        Tests pytest (reproductibilité, critères d'acceptation)
output/       Résultats exportés (généré à l'exécution, non versionné)
```
#   a g e n t - s i m u l a t i o n  
 