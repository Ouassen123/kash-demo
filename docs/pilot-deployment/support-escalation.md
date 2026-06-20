# Pilot Support Escalation Procedures

## Severity Levels
- **SEV-1**: Full outage for one or both schools (API unreachable, data corruption risk)
- **SEV-2**: Major degradation (p95 > 200ms, error rate > 5%, critical feature broken)
- **SEV-3**: Minor issue/workaround available

## Escalation Matrix
1. **L1 School IT Support**
   - Validate user-side and network-side symptoms
   - Open ticket with context and timestamps
2. **L2 Platform Ops**
   - Inspect infra, logs, health endpoints, dashboards
   - Trigger rollback/restart if needed
3. **L3 Engineering**
   - Root cause analysis and permanent fix
   - Post-incident report within 24h

## On-call Contact Workflow
- Pager/Alert webhook receives alerts from Alertmanager
- Acknowledge alert in <5 min for SEV-1/SEV-2
- Initiate status update every 15 min until mitigation

## Required Ticket Template
- School: `school-a` or `school-b`
- Severity
- Impacted feature/API endpoint
- Start time (UTC)
- Evidence (logs, screenshots, trace IDs)
- Mitigation applied
- Next actions
