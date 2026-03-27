# Team Git Rules

## 1) Never push directly to `main`
Every change goes through a branch and pull request.

## 2) Use small branches
Branch names:
- `feature/intake-*`
- `feature/planning-*`
- `feature/tracking-*`
- `feature/driver-*`
- `fix/*`
- `chore/*`

## 3) Stay in your area unless coordinated
Default file ownership:
- `app/models`, `app/repositories`, `alembic` -> Krishi
- `app/integrations`, `contracts` -> Mihir
- `.github`, Docker, env/setup -> Mehak and Ceren
- `tests` -> Andy
- `adr`, cross-cutting structure -> Rishi
- `driver_ui` -> whoever is assigned driver-flow work for that task

If you need to edit another person's main area, message them first.

## 4) One branch = one focused task
Do not mix schema, CI, UI, and unrelated API changes in one PR.

## 5) Pull before starting work
Before coding:
```bash
git checkout main
git pull origin main
git checkout -b feature/your-branch-name
```

## 6) Rebase or merge main frequently
Sync your branch daily if work is ongoing.

## 7) PR checklist is mandatory
A PR should include:
- what changed
- which folder(s) changed
- which endpoint or UI page changed
- test proof or screenshots
- migration note if DB changed
- contract note if request/response changed

## 8) Schema and contract changes need extra discipline
If you change:
- DB schema -> update migration and notify Krishi
- external API contract -> update `contracts/` and notify Mihir + Rishi
- CI or Docker -> notify Mehak/Ceren
- tests/coverage -> notify Andy

## 9) No silent breaking changes
Use additive changes first. Do not rename or remove API fields casually.

## 10) Keep placeholder data separate from real logic
Do not leave random hardcoded demo data inside service files once real DB logic is added.

## 11) Commit messages should be clean
Examples:
- `feat: add intake endpoint for delivery request snapshot`
- `feat: add customer sync client and schemas`
- `test: add tracking endpoint tests`
- `chore: add CI pytest workflow`
- `refactor: move routing logic into planning service`

## 12) Before opening PR
Run:
```bash
pytest
```
If you changed formatting or imports, clean those too.
