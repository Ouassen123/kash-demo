# Rapport — État du Système KASH Platform

**Date :** 26 juillet 2026  
**Version analysée :** Backend FastAPI + Frontend Next.js 14

---

## 1. État Actuel par Module KASH

### K — Knowledge (Analyse CV)

| Composant | Statut | Détails |
|-----------|--------|---------|
| Upload CV (PDF/DOCX/TXT) | ✅ Fonctionnel | Extraction texte via `pypdf` / `python-docx` |
| ML Model (TF-IDF + KNN) | ⚠️ Partiel | Modèle entraîné mais `scikit-learn` version incompatibilité → fallback keyword |
| Détection filière | ✅ Fonctionnel (fallback) | Keyword matching sur 6 domaines (electrical, mechanical, quality, logistics, management, software) |
| Détection tech domains | ✅ Fonctionnel | `_TECH_KEYWORDS` avec ~60+ mots-clés |
| Schéma API `KnowledgeScoreResponse` | ✅ Corrigé | Ajout de `predicted_filiere`, `detected_tech_domains` + `extra='allow'` |
| Frontend `/kash/start` | ✅ Corrigé | Filière + challenges s'affichent après upload CV |
| Admin Model Test Lab | ✅ Fonctionnel | Upload PDF, prediction filière, recommandation challenges |

### A — Attitude (Quiz cognitif + Psychometric)

| Composant | Statut | Détails |
|-----------|--------|---------|
| Quiz cognitif adaptatif | ✅ Fonctionnel | 5 questions, scoring, difficulté adaptative |
| Questions psychométriques (Habits) | ✅ Intégré | 20 questions Likert (Big Five, Grit, Self-Discipline) chargées après quiz |
| Soumission psychometric | ✅ Intégré | POST `/habits/psychometric/submit` → profil complet |
| Affichage scores combinés | ✅ Fonctionnel | Score cognitif + score Habits affichés |

### S — Skills (Challenges pratiques)

| Composant | Statut | Détails |
|-----------|--------|---------|
| Challenges par domaine | ✅ Fonctionnel | 6 challenges : electrical (2), mechanical (1), quality (1), logistics (1), management (1) |
| Scoring sémantique | ⚠️ Basique | Keyword matching (60%) + word overlap (40%), pas de NLP avancé |
| Chargement auto après CV | ✅ Corrigé | Fallback : charge tous les challenges si aucun domaine détecté |
| Soumission réponses | ✅ Fonctionnel | POST `/skills/practical/submit` |

### H — Habits (Entretien multimodal)

| Composant | Statut | Détails |
|-----------|--------|---------|
| Entretien multimodal | ✅ Refactorisé | Recording continu (un seul recorder, pas de stop/relance par question) |
| Label "Habits" | ✅ Affiché | Progress bar + section + recorder |
| Réponse texte et/ou oral | ✅ Fonctionnel | Texte ≥10 chars OU audio capturé |
| Analyse multimodale | ✅ Fonctionnel | `analyzeHabitsInterview` avec audio + video frames |
| WebcamAudioRecorder | ✅ Fonctionnel | Capture audio + frames vidéo en base64 |

### Intelligence (Scoring global)

| Composant | Statut | Détails |
|-----------|--------|---------|
| KASH scoring | ✅ Fonctionnel | Pondération Knowledge 30% + Attitude 40% + Skills 30% |
| SHAP explanations | ✅ Backend | Feature importance calculé |
| Frontend insights | ✅ Basique | Redirection vers `/intelligence/insights` |

### Attitude (Module séparé)

| Composant | Statut | Détails |
|-----------|--------|---------|
| Backend API | ✅ Fonctionnel | Questions + analyse multimodale |
| Frontent integration | ❌ Manquant | Non intégré dans le journey `/kash/start` |

---

## 2. Faiblesses Détectées

### 🔴 Critique

1. **Firebase Admin SDK échoue au démarrage**
   - `Failed to initialize Firebase: Unable to load PEM file`
   - L'auth fonctionne en mode debug (fallback dev user) mais **échouera en production**
   - Fichier : `src/core/auth.py:47`

2. **spaCy non installé**
   - `spaCy model not found. Falling back to lightweight blank English tokenizer`
   - Impact : analyse NLP des CVs et entretiens **dégradée** (pas de POS tagging, NER, lemmatisation)
   - Fichiers : `src/modules/knowledge/cv_parser.py`, `src/modules/knowledge/nlp/cv_analyzer.py`, `src/modules/habits/habits_service.py`

3. **Modèle ML Knowledge — incompatibilité scikit-learn**
   - Le modèle entraîné ne se charge pas correctement (version sklearn mismatch)
   - Fallback keyword fonctionne mais **moins précis** que TF-IDF + KNN
   - Fichier : `src/modules/knowledge/ml/knowledge_model.py`

### 🟡 Moyen

4. **Aucun test automatisé intégré**
   - 37 fichiers de test existent mais **pas de pytest configuré** (pas de `pytest.ini`, `conftest.py` minimal)
   - Pas de CI/CD pipeline
   - Risque de régression élevé à chaque modification

5. **Scoring des challenges pratiques trop basique**
   - `_score_text_answer` : keyword matching (60%) + word overlap (40%)
   - Pas de similarité sémantique (pas de sentence embeddings, pas de BERT/sentence-transformers)
   - Risque : fausses réponses bien scorées si elles contiennent les bons mots-clés

6. **Module Attitude non intégré au journey frontend**
   - Backend complet (questions, analyse multimodale, scoring)
   - Mais **pas utilisé** dans `/kash/start` — le journey saute d'Attitude → Knowledge → Habits → Skills
   - L'Attitude est un des 4 piliers KASH mais n'est pas évalué dans le flow étudiant

7. **Dépendances manquantes (aiohttp)**
   - `aiohttp` n'était pas installé → crash backend au démarrage
   - Indique un `requirements.txt` incomplet ou non respecté
   - Fichier : `src/integration/esco_client.py`

8. **Pas de persistance des résultats psychometric**
   - Le score psychometric est affiché dans le frontend mais **non sauvegardé** en base
   - Pas d'enregistrement `UserAssessment` créé pour le psychometric
   - Si l'utilisateur rafraîchit la page, le score est perdu

9. **Interview questions hardcodées (3 questions)**
   - `interviewQuestions` défini en dur dans `kash-journey-runner.tsx` (3 questions)
   - Pas chargées depuis l'API backend `/habits/interview/questions`
   - Pas adaptatives au domaine détecté

10. **Intelligence assessment — career_goals hardcodés**
    - `generateIntelligenceAssessment({ industry: 'technology', career_goals: ['software_engineer'] })`
    - Industry et career_goals **non adaptés** au domaine détecté du CV
    - Un étudiant en Génie Électrique sera évalué contre `software_engineer`

### 🟢 Mineur

11. **Encodage caractères français**
    - Les réponses des challenges contiennent des `Ã©` au lieu de `é` (problème d'encodage UTF-8/Latin-1)
    - Visible dans la sortie API des challenges pratiques

12. **Frontend — pas de gestion d'erreur utilisateur**
    - Si l'API retourne une erreur, le message technique s'affiche (`Échec analyse multimodale`)
    - Pas de retry, pas de message friendly

13. **Logs bruyants**
    - `app.log` contient 1549 lignes Firebase + 164 lignes spaCy
    - Pas de rotation de logs configurée

---

## 3. Recommandations

### 🔴 URGENT (à faire immédiatement)

| # | Recommandation | Effort | Impact |
|---|----------------|--------|--------|
| U1 | **Corriger Firebase Admin SDK** — régénérer le fichier PEM ou utiliser une variable d'environnement pour le credentials JSON | 1h | Auth production cassée sans ça |
| U2 | **Installer spaCy + modèle** — `pip install spacy && python -m spacy download en_core_web_sm` | 15min | NLP dégradé sur tous les modules |
| U3 | **Réparer/retravailler le modèle ML Knowledge** — vérifier version sklearn, retrain, ou fixer la version dans requirements.txt | 2-4h | Précision filière critique pour tout le flow |
| U4 | **Compléter requirements.txt** — ajouter `aiohttp`, `spacy`, vérifier toutes les dépendances | 30min | Backend crash au démarrage |

### 🟡 MOYEN (à planifier)

| # | Recommandation | Effort | Impact |
|---|----------------|--------|--------|
| M1 | **Intégrer le module Attitude dans le journey** — ajouter une étape "Attitude" entre Knowledge et Habits dans `kash-journey-runner.tsx` | 4-6h | KASH complet (4 piliers au lieu de 3) |
| M2 | **Persister les résultats psychometric** — créer un `UserAssessment` dans le backend `/habits/psychometric/submit` | 2h | Scores perdus au refresh |
| M3 | **Charger les questions d'entretien depuis l'API** — remplacer les 3 questions hardcodées par un fetch vers `/habits/interview/questions` | 2h | Questions adaptatives et maintenables |
| M4 | **Rendre Intelligence adaptatif** — utiliser le domaine détecté pour `industry` et `career_goals` au lieu de `technology` / `software_engineer` | 2h | Scoring global incorrect pour non-informaticiens |
| M5 | **Améliorer le scoring des challenges** — intégrer `sentence-transformers` pour similarité sémantique au lieu de keyword matching | 4-6h | Évaluation plus juste |
| M6 | **Mettre en place pytest + CI** — configurer `pytest.ini`, ajouter tests E2E pour le journey complet | 1 jour | Prévention des régressions |

### 🟢 LONG TERME (amélioration continue)

| # | Recommandation | Effort | Impact |
|---|----------------|--------|--------|
| L1 | **Ajouter plus de challenges par domaine** — actuellement 1-2 par domaine, viser 5+ | 2-3 jours | Meilleure couverture d'évaluation |
| L2 | **Entretien multimodal — analyse temps réel** — implémenter WebSocket pour analyse streaming au lieu de soumission finale | 1 semaine | Feedback instantané pendant l'entretien |
| L3 | **Tableau de bord étudiant** — page de suivi des scores KASH dans le temps | 3-5 jours | UX améliorée |
| L4 | **Internationalisation (i18n)** — le système mixe français/anglais, formaliser | 2-3 jours | Cohérence linguistique |
| L5 | **Corriger l'encodage UTF-8** — auditer toutes les chaînes qui passent entre Python et JSON | 1h | Affichage propre des caractères français |

---

## 4. Architecture — Flow Actuel du Journey Étudiant

```
/kash/start
    │
    ├─ 1. Attitude (quiz cognitif 5 questions)
    │      └─ + Habits Psychometric (20 questions Likert)
    │
    ├─ 2. Knowledge (upload CV)
    │      ├─ Extraction texte (PDF/DOCX/TXT)
    │      ├─ ML Model → filière + tech domains
    │      └─ Auto-load challenges pratiques adaptés
    │
    ├─ 3. Habits (entretien multimodal continu)
    │      ├─ WebcamAudioRecorder (audio + vidéo)
    │      ├─ 3 questions comportementales
    │      └─ Analyse multimodale (texte + audio + frames)
    │
    ├─ 4. Skills (challenges pratiques)
    │      ├─ Challenge du domaine détecté
    │      ├─ Réponses textuelles
    │      └─ Scoring sémantique (keyword + overlap)
    │
    └─ Intelligence (scoring global KASH)
           ├─ Knowledge 30% + Attitude 40% + Skills 30%
           └─ Redirection /intelligence/insights
```

**Manque :** L'étape Attitude (entretien comportemental) existe en backend mais n'est pas dans le flow.

---

## 5. Matrice de Dépendances Critiques

```
spaCy ──────────┬── Knowledge (CV parsing, NER, POS)
                 ├── Habits (analyse réponses, clarity scoring)
                 └── Attitude (analyse émotions, stress)

scikit-learn ───┬── Knowledge ML Model (TF-IDF, KNN, classifier)
                 └── Intelligence (predictive model)

Firebase Admin ──┴── Auth (tous les endpoints protégés)

aiohttp ────────┬── ESCO Client (skill matching)
                 └── GitHub Client (code analysis)
```

---

## 6. Conclusion

Le système KASH est **fonctionnel en mode développement** mais présente plusieurs faiblesses qui l'empêcheraient de fonctionner correctement en production :

- **3 dépendances critiques manquantes** (Firebase, spaCy, aiohttp)
- **1 module KASH non intégré** (Attitude)
- **Scores non persistés** (psychometric)
- **Scoring basique** (keyword matching au lieu de NLP sémantique)
- **Pas de tests automatisés**

Les corrections urgentes (U1-U4) peuvent être faites en **moins d'une journée** et débloqueront le système pour des tests réels. Les recommandations moyennes (M1-M6) nécessitent **1-2 semaines** pour un système robuste et complet.
