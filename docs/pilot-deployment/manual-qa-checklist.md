# Manual QA Checklist for Pilot Go/No-Go

## Scope
Covers validation of Knowledge, Abilities, Skills, and Intelligence flows before pilot activation.

## Reviewer Metadata
- Reviewer:
- Pilot site: school-a / school-b
- Dataset snapshot:
- Date (UTC):

## Knowledge Module
- [ ] CV ingestion returns normalized profile
- [ ] ESCO mapping is generated with non-empty top skill categories
- [ ] Recommendation payload includes at least one action item

## Abilities Module
- [ ] Adaptive quiz can be started/completed end-to-end
- [ ] Domain scores persist and appear on dashboard
- [ ] Feedback text is visible and coherent

## Skills Module
- [ ] Skills profile endpoint returns language distribution
- [ ] Top skills confidence values are present and bounded [0,1]
- [ ] Deep dive page renders without client error

## Intelligence Module
- [ ] Overall KASH score is generated
- [ ] Explainability output includes feature importance
- [ ] Career suggestions are produced with confidence labels

## Operations & Compliance
- [ ] Health endpoint returns healthy or degraded-with-reason
- [ ] Metrics endpoint is scraped in Prometheus
- [ ] Access to sensitive logs is role-restricted
- [ ] Validation artifacts are exported (JSON + CSV)

## Sign-off
- Decision: GO / NO-GO
- Blocking issues:
- Follow-up actions:
