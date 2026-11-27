# Deployment, Admin Testing & Backup Guide

## 1. Quick Local Mode (Windows)
1. Seed the demo admin, 3 test users, demo runs, and `WELCOME20` coupon:
   ```powershell
   cd backend
   .\.venv\Scripts\python.exe seed.py
   ```
2. Start backend (`uvicorn app.main:app --port 8000`) and frontend (`npm run dev`).
3. Admin login credentials (seeded):
   - **Email**: `admin@leadharvest.in`
   - **Password**: `Admin@LeadHarvest2026!`
   - **Admin URL**: `http://localhost:3000/admin`

## 2. Production Docker Compose (VPS)
1. Copy `.env.example` to `.env` and set strong `LEADHARVEST_SECRET_KEY`, `POSTGRES_PASSWORD`, and Razorpay keys.
2. Run:
   ```bash
   docker compose up -d --build
   docker exec -it leadharvest_api alembic upgrade head
   docker exec -it leadharvest_api python seed.py
   ```

## 3. Daily Database Backup & Restore
- **Backup** (add to cron `0 2 * * *`):
  ```bash
  bash backend/scripts/backup_db.sh
  ```
- **Restore**:
  ```bash
  gunzip -c backups/leadharvest_YYYY-MM-DD_HHMMSS.sql.gz | docker exec -i leadharvest_postgres psql -U leadharvest leadharvest
  ```

## 4. Extending States, Categories, Plans, Filters & Adapters
- **States/Cities**: Edit `config/india_locations.json` and `backend/config/india_locations.json`.
- **Categories**: Edit `config/categories.json` and `backend/config/categories.json`.
- **Plans & Prices**: Edit directly in `/admin` → **Plans & Coupons** (no code changes needed).
- **Smart Filters**: Add filter rules in `backend/app/services/lead_filters.py`.
- **Source Adapters**: Subclass `BaseSourceAdapter` in `backend/app/adapters/` and declare `capabilities()`.
