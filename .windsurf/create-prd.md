---
description: Interactive PRD creation workflow for KASH Career Intelligence Platform
---

# Create PRD - Interactive Workflow

## Purpose
Transform the product brief into a comprehensive Product Requirements Document (PRD) with detailed specifications, user stories, and technical requirements.

## Interactive Steps

### Step 1: User Research & Personas
**Questions to answer:**
- Who are the primary users? (students, administrators, career counselors)
- What are their pain points with current solutions?
- What are their success metrics?

### Step 2: Feature Specification
**For each MVP feature:**
- Detailed functional requirements
- User stories (As a [user], I want [goal] so that [benefit])
- Acceptance criteria
- Technical constraints

### Step 3: Risk Assessment
**Risk Matrix:**
| Risk | Impact | Probability | Priority | Status |
|------|--------|-------------|----------|--------|
| Model Accuracy | Élevé | Moyenne | P1 | Monitoring |
| Algorithmic Bias | Très Élevé | Moyenne | P1 | Mitigation |
| Student Adoption | Élevé | Moyenne | P2 | In Progress |
| Data Quality | Élevé | Moyenne | P2 | Monitoring |
| Student Churn Post-Evaluation | Moyen | Élevée | P2 | Planning |
| Tests Reliability (Abilities/Skills) | Moyen | Moyenne | P3 | Monitoring |
| Advisor/Mentor Adoption | Moyen | Moyenne | P3 | Planning |
| Partner Acquisition | Élevé | Moyenne | P3 | Planning |
| GDPR Compliance | Élevé | Faible | P3 | Implemented |
| Integration Failures | Moyen | Faible | P4 | Monitoring |
| Scaling Performance | Moyen | Moyenne | P4 | Planning |

### Step 4: Technical Architecture
**Components to define:**
- System architecture diagram
- Data models for KASH dimensions
- API specifications
- Integration points (ESCO/O*NET, GitHub, etc.)

### Step 4: Success Metrics & KPIs
**Detailed metrics:**
- User engagement metrics
- Technical performance metrics
- Business metrics
- Scientific validation metrics

### Step 5: Risk Assessment
**Areas to analyze:**
- Technical risks (ML model accuracy, data quality)
- Business risks (adoption, competition)
- Ethical risks (bias, privacy)
- Mitigation strategies

### Additional Risks Identified:

**Risk 9: Student Churn Post-Evaluation**
- **Impact**: Moyen - réduit l'engagement long terme
- **Probability**: Élevée - comportement naturel après première évaluation
- **Mitigation**:
  - Notifications régulières de progression KASH
  - Nouveaux contenus et défis mensuels
  - Gamification avec badges et niveaux

**Risk 10: Tests Reliability (Abilities/Skills)**
- **Impact**: Moyen - affecte confiance dans les scores
- **Probability**: Moyenne - variabilité naturelle des tests
- **Mitigation**:
  - Tests multiples par dimension avec moyennage
  - Calibration régulière contre benchmarks
  - Intervalles de confiance affichés

**Risk 11: Advisor/Mentor Adoption**
- **Impact**: Moyen - critique pour écosystème KASH
- **Probability**: Moyenne - dépend de valeur perçue
- **Mitigation**:
  - Interface simplifiée pour conseillers
  - Analytics sur progression étudiants
  - Commission sur coaching premium

## Output
Complete PRD document ready for development team handoff.

## Usage
Run `/create-prd --interactive` to start the guided PRD creation process.