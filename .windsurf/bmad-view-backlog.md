---
description: Interactive backlog viewer and management for KASH Platform development
---

# BMAD View Backlog - Interactive Workflow

## Purpose
Visualize, prioritize, and manage the product backlog for KASH Career Intelligence Platform development across all sprints.

## Interactive Backlog Management

### Current Sprint Status
**Sprint**: 0 - Setup & Foundation
**Duration**: 2 semaines
**Status**: Planning

### Backlog Categories

#### **🏗️ Infrastructure & Setup**
- [ ] Repository setup (frontend, backend, ML)
- [ ] CI/CD pipeline configuration
- [ ] Cloud infrastructure deployment
- [ ] Database schema setup
- [ ] Development environment templates

#### **🧠 Module Knowledge**
- [ ] NLP CV analysis engine
- [ ] ESCO/O*NET integration
- [ ] Adaptive quiz algorithm
- [ ] Knowledge scoring calculation
- [ ] Frontend evaluation interface

#### **🎯 Module Abilities**
- [ ] Text-based cognitive tests
- [ ] Analytical scenarios engine
- [ ] Voice recording interface
- [ ] Speech-to-text integration
- [ ] Multimodal fusion algorithm

#### **⚡ Module Skills**
- [ ] Mini-projects evaluation
- [ ] GitHub API integration
- [ ] Code analysis algorithm
- [ ] Portfolio parsing
- [ ] Skills scoring system

#### **🔄 Mapping & Intelligence**
- [ ] Job database (50 métiers)
- [ ] Compatibility scoring algorithm
- [ ] ML prediction models
- [ ] Explainability engine (SHAP)
- [ ] Success probability calculation

#### **📊 Admin & Reporting**
- [ ] Admin dashboard interface
- [ ] Cohort management system
- [ ] Statistics calculation engine
- [ ] Report generation (PDF/CSV)
- [ ] User management system

#### **🧪 Testing & Quality**
- [ ] Unit tests templates
- [ ] Integration tests
- [ ] Performance tests
- [ ] Security audit
- [ ] User acceptance testing

## Interactive Commands

### `--view-sprint [number]`
View detailed backlog for specific sprint
Example: `/bmad-view-backlog --view-sprint 1`

### `--priority [category]`
View prioritized items by category
Example: `/bmad-view-backlog --priority infrastructure`

### `--status [filter]`
Filter backlog by status
Options: `todo`, `in-progress`, `done`, `blocked`
Example: `/bmad-view-backlog --status in-progress`

### `--estimate`
View story points and time estimates
Example: `/bmad-view-backlog --estimate`

### `--dependencies`
View task dependencies across sprints
Example: `/bmad-view-backlog --dependencies`

### `--risks`
View risks associated with backlog items
Example: `/bmad-view-backlog --risks`

## Backlog Metrics

### **Current Status**
- Total items: 35
- Completed: 0
- In Progress: 0
- Blocked: 0
- Story Points: 280

### **Sprint Distribution**
- Sprint 0: 8 items (64 points)
- Sprint 1-2: 5 items (40 points)
- Sprint 3-4: 5 items (40 points)
- Sprint 5-6: 5 items (40 points)
- Sprint 7-8: 5 items (40 points)
- Sprint 9: 4 items (32 points)
- Sprint 10: 4 items (32 points)
- Sprint 11: 5 items (40 points)
- Sprint 12: 4 items (32 points)

## Usage Examples

1. **View current sprint backlog**:
   `/bmad-view-backlog --view-sprint 0`

2. **Check infrastructure priorities**:
   `/bmad-view-backlog --priority infrastructure`

3. **See blocked items**:
   `/bmad-view-backlog --status blocked`

4. **Review time estimates**:
   `/bmad-view-backlog --estimate`

5. **Check dependencies**:
   `/bmad-view-backlog --dependencies`

## Next Steps

1. Choose sprint to focus on
2. Review priorities and dependencies
3. Assign team members
4. Start sprint execution
5. Track progress daily

## Integration with Sprint Roadmap

This backlog viewer integrates with the sprint roadmap defined in `sprint-roadmap.md`:
- Each sprint has defined deliverables
- Dependencies are tracked across sprints
- Risk mitigation is built into priorities
- Success metrics are monitored per sprint

Run `/bmad-view-backlog --interactive` to start interactive backlog management session.