# Pilot Deployment Runbook (School A + School B)

## 1) Prerequisites
- Docker Engine + Docker Compose plugin
- DNS entries for:
  - `api.school-a.kash.local`
  - `api.school-b.kash.local`
- TLS certificates at:
  - `/etc/ssl/school-a/fullchain.pem`, `/etc/ssl/school-a/privkey.pem`
  - `/etc/ssl/school-b/fullchain.pem`, `/etc/ssl/school-b/privkey.pem`

## 2) Environment Setup
1. Copy env templates:
   - `deploy/pilot/.env.school-a.example` -> `deploy/pilot/.env.school-a`
   - `deploy/pilot/.env.school-b.example` -> `deploy/pilot/.env.school-b`
2. Set strong secrets for DB, Redis, JWT and Grafana admin.

## 3) Deploy Pilot Stack
```bash
docker compose -f infrastructure/pilot/docker-compose.pilot.yml --env-file deploy/pilot/.env.school-a --env-file deploy/pilot/.env.school-b up -d
```

## 4) Verify Health
- School A API: `http://localhost:8100/health`
- School B API: `http://localhost:8200/health`
- Prometheus: `http://localhost:9190`
- Grafana: `http://localhost:3200`
- Jaeger: `http://localhost:17686`

## 5) School Isolation Validation
- Confirm each API points to its own DB + Redis URL in container env.
- Execute data writes on School A and verify absence in School B.
- Confirm each API exports metrics with `school` label.

## 6) Backup and Restore
- Backup:
  - `infrastructure/pilot/backup/backup_postgres.sh school-a`
  - `infrastructure/pilot/backup/backup_postgres.sh school-b`
- Restore:
  - `infrastructure/pilot/backup/restore_postgres.sh school-a <backup-file>`
  - `infrastructure/pilot/backup/restore_postgres.sh school-b <backup-file>`

## 7) Incident Procedure
- Check alerts in Grafana + Prometheus
- Check API logs: `docker logs kash-school-a-api` / `docker logs kash-school-b-api`
- Escalate per `docs/pilot-deployment/support-escalation.md`
