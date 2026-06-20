---
description: KASH Platform Sprint Roadmap - 12 Sprints to MVP
---

# KASH Platform Sprint Roadmap

## Overview
12 sprints de 2 semaines = 6 mois pour livrer le MVP complet de la KASH Career Intelligence Platform

## Sprint Planning

### **Sprint 0 → Setup & Foundation (2 semaines)**
**Objectif**: Infrastructure et base technique prête

**User Stories:**
- En tant que développeur, je veux un environnement de développement configuré
- En tant que développeur, je veux des pipelines CI/CD fonctionnels
- En tant que développeur, je veux des templates de tests KASH

**Tâches:**
- [ ] Setup repos Git (frontend, backend, ML)
- [ ] Configuration CI/CD (GitHub Actions)
- [ ] Infrastructure cloud (AWS/Azure)
- [ ] Base de données PostgreSQL setup
- [ ] Templates tests unitaires/intégration
- [ ] Documentation technique initiale

**Deliverables:**
- ✅ Infrastructure déployée
- ✅ CI/CD fonctionnel
- ✅ Base de tests KASH

---

### **Sprint 1-2 → Module Knowledge (4 semaines)**
**Objectif**: Évaluation complète dimension Knowledge

**User Stories:**
- En tant qu'étudiant, je veux évaluer mes connaissances académiques
- En tant qu'étudiant, je veux analyser mon CV via NLP
- En tant qu'étudiant, je veux passer des quiz adaptatifs

**Tâches:**
- [ ] NLP CV analysis engine
- [ ] Mapping ESCO/O*NET integration
- [ ] Quiz adaptatif algorithm
- [ ] Knowledge scoring calculation
- [ ] Frontend évaluation Knowledge
- [ ] Tests unitaires Knowledge

**Deliverables:**
- ✅ Module Knowledge fonctionnel
- ✅ Integration ESCO/O*NET
- ✅ Scoring Knowledge validé

---

### **Sprint 3-4 → Module Attitude Phase 1 (NLP seulement) (4 semaines)**
**Objectif**: Évaluation Abilities via texte uniquement

**User Stories:**
- En tant qu'étudiant, je veux évaluer mes aptitudes via tests textuels
- En tant qu'étudiant, je veux résoudre des scénarios analytiques

**Tâches:**
- [ ] Tests cognitifs text-based
- [ ] Scénarios analytiques engine
- [ ] Résolution problèmes algorithm
- [ ] Abilities scoring NLP
- [ ] Frontend évaluation Abilities
- [ ] Validation modèle Abilities

**Deliverables:**
- ✅ Module Abilities NLP fonctionnel
- ✅ Tests cognitifs déployés
- ✅ Scoring Abilities validé

---

### **Sprint 5-6 → Module Attitude Phase 2 (texte + voix) (4 semaines)**
**Objectif**: Extension Abilities avec multimodal

**User Stories:**
- En tant qu'étudiant, je veux évaluer mes aptitudes via voix
- En tant qu'étudiant, je veux une analyse multimodal complète

**Tâches:**
- [ ] Voice recording interface
- [ ] Speech-to-text integration
- [ ] Multimodal fusion algorithm
- [ ] Enhanced Abilities scoring
- [ ] Frontend voice evaluation
- [ ] Tests multimodal

**Deliverables:**
- ✅ Module Abilities multimodal
- ✅ Voice evaluation déployée
- ✅ Fusion algorithm validée

---

### **Sprint 7-8 → Module Skills (4 semaines)**
**Objectif**: Évaluation compétences pratiques

**User Stories:**
- En tant qu'étudiant, je veux évaluer mes skills via mini-projets
- En tant qu'étudiant, je veux analyser mon code/portfolio GitHub

**Tâches:**
- [ ] Mini-projets evaluation engine
- [ ] GitHub integration API
- [ ] Code analysis algorithm
- [ ] Portfolio parsing
- [ ] Skills scoring calculation
- [ ] Frontend évaluation Skills

**Deliverables:**
- ✅ Module Skills fonctionnel
- ✅ GitHub integration active
- ✅ Code analysis validé

---

### **Sprint 9 → Mapping KASH-Métiers (2 semaines)**
**Objectif**: Connecter profils KASH aux métiers

**User Stories:**
- En tant qu'étudiant, je veux découvrir les métiers compatibles
- En tant qu'étudiant, je veux voir les scores de compatibilité

**Tâches:**
- [ ] Job database (50 métiers)
- [ ] Compatibility scoring algorithm
- [ ] KASH-job matching engine
- [ ] Frontend interface métiers
- [ ] Filters et recherche
- [ ] Export résultats

**Deliverables:**
- ✅ Base métiers complète
- ✅ Algorithm matching fonctionnel
- ✅ Interface recherche déployée

---

### **Sprint 10 → Prédiction & IA Explicable (2 semaines)**
**Objectif**: Modèles prédictifs avec transparence

**User Stories:**
- En tant qu'étudiant, je veux connaître ma probabilité de réussite
- En tant qu'étudiant, je veux comprendre pourquoi chaque recommandation

**Tâches:**
- [ ] ML model training pipeline
- [ ] Success prediction algorithm
- [ ] Explainability engine (SHAP)
- [ ] Visualisation explications
- [ ] Frontend predictions
- [ ] Validation accuracy >70%

**Deliverables:**
- ✅ Modèle prédictif déployé
- ✅ IA explicable fonctionnelle
- ✅ Accuracy target atteinte

---

### **Sprint 11 → Admin & Reporting (2 semaines)**
**Objectif**: Interface administration et rapports

**User Stories:**
- En tant qu'administratrice, je veux gérer les cohortes étudiantes
- En tant qu'administratrice, je veux générer des rapports statistiques

**Tâches:**
- [ ] Admin dashboard interface
- [ ] Cohort management system
- [ ] Statistics calculation engine
- [ ] Report generation (PDF/CSV)
- [ ] User management
- [ ] Permission system

**Deliverables:**
- ✅ Admin interface complète
- ✅ Rapports générables
- ✅ Gestion cohortes fonctionnelle

---

### **Sprint 12 → Validation & Optimisation (2 semaines)**
**Objectif**: Tests finaux et optimisations

**User Stories:**
- En tant qu'équipe, je veux valider tous les modules
- En tant qu'équipe, je veux optimiser les performances

**Tâches:**
- [ ] Integration testing complet
- [ ] Performance optimization
- [ ] Security audit
- [ ] User acceptance testing
- [ ] Documentation finale
- [ ] Deployment preparation

**Deliverables:**
- ✅ MVP validé et prêt
- ✅ Performance optimisée
- ✅ Documentation complète

---

## Milestones & Gates

| Milestone | Sprint | Validation Criteria |
|-----------|--------|---------------------|
| **Foundation Ready** | Sprint 0 | Infrastructure + CI/CD opérationnels |
| **Knowledge Module** | Sprint 2 | Tests Knowledge validés |
| **Abilities Module** | Sprint 6 | Multimodal fusion fonctionnelle |
| **Skills Module** | Sprint 8 | GitHub integration active |
| **Matching Engine** | Sprint 9 | KASH-métiers mapping validé |
| **ML Predictions** | Sprint 10 | Accuracy >70% atteinte |
| **Admin Ready** | Sprint 11 | Interface admin complète |
| **MVP Complete** | Sprint 12 | Tests finaux validés |

## Success Metrics per Sprint

- **Velocity**: Points/story par sprint
- **Quality**: % tests passants
- **Performance**: Temps réponse <2s
- **User Feedback**: Score satisfaction >4/5

## Risk Mitigation Timeline

- **Sprint 0-2**: Infrastructure risks
- **Sprint 3-6**: ML model accuracy risks  
- **Sprint 7-8**: Integration risks
- **Sprint 9-10**: User adoption risks
- **Sprint 11-12**: Performance/security risks
