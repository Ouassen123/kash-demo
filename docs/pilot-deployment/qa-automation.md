# QA Automation - Final Validation Workspace

## Purpose
This automation runs final cross-module checks and writes audit-friendly artifacts (JSON + CSV) for pilot sign-off.

## Command
```bash
python scripts/run_final_validation.py
```

## Outputs
Generated in `./qa-results/`:
- `validation_<pilot>_<timestamp>.json`
- `validation_<pilot>_<timestamp>.csv`
- `manual_checklist.json`
- `validation_audit.json`

## Reviewer workflow
1. Run automation script.
2. Complete manual checklist in `docs/pilot-deployment/manual-qa-checklist.md`.
3. Attach generated files to pilot release ticket.
4. Mark GO/NO-GO in audit file and escalation notes.
