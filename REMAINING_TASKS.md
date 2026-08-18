# Remaining Tasks — MongoDB Migration (AyurDietPro)

Completed in this update: SQLite shim replaced with MongoDB (Motor + Beanie 1.x),
all routes/models refactored to async Beanie queries, `MONGODB_URI` loaded strictly
from environment, deps pinned, `.env.example` updated, docker-compose includes a
mongo service. Verified via full in-memory end-to-end test (auth, patients, foods,
plan generation/update, reports, admin).

## Before deploying

1. **Set production environment variables** on the hosting platform (e.g. Render):
   - `MONGODB_URI` — Atlas SRV string or managed MongoDB URI (REQUIRED, no default).
   - `MONGODB_DB` — optional, defaults to `ayurdiet`.
   - `SECRET_KEY` — a strong random value (was already required).
2. **Provision the MongoDB instance** (e.g. MongoDB Atlas free tier) and create a
   database user with readWrite access. Whitelist the backend's outbound IP if needed.
3. **Migrate existing data (optional)** — the old SQLite data in `server/ayurdiet.db`
   is NOT migrated automatically. If the existing users/patients/plans matter, write
   a one-off migration script (read SQLite `documents` table -> insert into MongoDB).
   Seed data (admin/doctor users, templates, foods) is recreated automatically on startup.
4. **Remove the legacy DB from git tracking** (file stays on disk, now gitignored):
   `git rm --cached server/ayurdiet.db`
5. **Local dev setup**: copy `server/.env.example` to `server/.env`, set a local
   `MONGODB_URI` (e.g. `mongodb://127.0.0.1:27017` or an Atlas dev cluster), then
   `uvicorn main:app --reload` in `server/`. Alternatively `docker compose up`
   (spins up its own mongo container).

## Testing / verification still to do

6. Run the backend against a **real MongoDB** (local or Atlas) and smoke-test:
   register -> login -> create patient -> generate diet plan -> edit plan -> weekly report
   -> admin stats. (Automated e2e passed against an in-memory mock only.)
7. Verify the deployed frontend can reach the backend (`VITE_API_URL` in
   `client/.env.production` currently points to the Render URL) and rebuild the
   client if that URL changes.

## Optional cleanups / improvements

8. `client/src/api.js` still contains a hardcoded `PROD_FALLBACK_BASE` fallback URL —
   consider removing it so the env var is the single source of truth.
9. Change the seeded default credentials (`admin@ayurdiet.com` / `admin1234`,
   `doctor@ayurdiet.com` / `demo1234`) or gate seeding behind an env flag before
   going fully public.
10. Consider adding a CI step that runs the e2e test (`mongomock-motor` currently
    installed locally only) and pinning `mongomock-motor` in a dev-requirements file.
11. `server/Dockerfile` uses `python:3.10-slim`; consider bumping to 3.12 to match
    the local dev environment.

## Commit & push (when ready)

```bash
git add .gitignore docker-compose.yml server/ client/
git rm --cached server/ayurdiet.db          # untrack legacy SQLite file
git commit -m "Replace SQLite shim with MongoDB (Motor + Beanie)"
git push
```
