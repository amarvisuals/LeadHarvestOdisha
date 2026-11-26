# LeadHarvest Odisha – One-Click Business Lead Data Collector

> A modern, calm, trustworthy lead collection and 3-tier deduplication platform built specifically for businesses operating across Odisha, India.

![LeadHarvest Odisha](https://img.shields.io/badge/Region-Odisha%2C%20India-teal?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-14%20App%20Router-000000?style=for-the-badge&logo=next.js&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Tailwind](https://img.shields.io/badge/Tailwind_CSS-3.4-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)

---

## Key Features

1. **All-Odisha Location Selector**:
   - Includes all 30 districts and major commercial towns (Bhubaneswar, Cuttack, Puri, Rourkela, Berhampur, Sambalpur, Balasore, Jeypore, Angul, Paradip, etc.).
   - Multi-select with instant search, "Select All Odisha" toggle (default: ALL selected), and clear button.
   - Configured via JSON (`config/odisha_locations.json`) for zero-code modifications.

2. **Smart Category Selector**:
   - 20+ pre-configured Odisha business sectors (Restaurants, Hotels, Gyms, Schools, Dentists, Real Estate, Wedding Planners, Car Dealers, Printing Presses, etc.).
   - Add custom categories with instant chip tagging.
   - Save and load reusable presets.

3. **Multi-File Deduplication & Audit**:
   - Drag-and-drop multiple `.xlsx`, `.xls`, `.csv` historical lead sheets at once.
   - Automatic audit card per file: valid rows, blank rows, invalid phone numbers, internal duplicates, and status badge ("Ready" / "Needs attention").
   - Fuzzy column detection ("Mobile", "Phone Number", "Firm", "Shop Name", "Town" auto-detected) with manual mapping override.
   - Merges into a persistent SQLite `Known Records` index.

4. **3-Tier Matching Algorithm**:
   1. Normalised 10-digit Indian mobile number comparison (`+91`, `0`, spaces stripped).
   2. Normalised business name + city exact match.
   3. Fuzzy token match (RapidFuzz `token_sort_ratio >= 90`) on name + address in the same city.

5. **Live Progress Experience**:
   - Animated SVG Hourglass with smooth falling sand grains and 180° rotation on loop.
   - Thick horizontal progress bar with soft glowing moving highlight on its tip.
   - Rotating dashed ring loader around hourglass + circular percentage ring.
   - 7-Stage Stepper: Preparing -> Searching -> Collecting -> Filtering -> Creating file -> Almost done -> Success.
   - Live metrics: Elapsed Time, Remaining Time estimate, Total Found, Duplicates Skipped, New Leads.
   - Pause, Resume, and Cancel (partial leads preserved) controls.
   - Celebratory checkmark drawing and confetti burst on completion.

6. **Styled 3-Sheet Excel Output**:
   - **Sheet 1: Leads**: Formatted header (Deep Teal `#0F766E`), frozen top row, auto-filter, auto-fitted column widths, clickable website and listing links.
   - **Sheet 2: Summary**: Search parameters, totals, duration, and engine metadata.
   - **Sheet 3: Skipped Duplicates**: Audit trail of every duplicate excluded and the matching rule/source.

---

## Quick Start on Windows

### Option A: One-Click Windows Batch File
Double click `run-windows.bat` in the project root:
```cmd
run-windows.bat
```
This automatically launches the FastAPI backend on port 8000 and the Next.js frontend on port 3000, then opens `http://localhost:3000` in your browser.

### Option B: Manual PowerShell Start

#### 1. Backend:
```powershell
cd backend
uv venv --python 3.11 .venv
.\.venv\Scripts\activate
uv pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

#### 2. Frontend:
```powershell
cd frontend
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000).

---

## Docker Compose Setup
Run both backend and frontend in isolated containers:
```bash
docker compose up --build
```
Access the application at `http://localhost:3000`.

---

## How to Customize

### Adding New Cities / Locations
Edit `config/odisha_locations.json`:
```json
{
  "id": "new_town",
  "name": "New Town",
  "district": "Khordha",
  "tier": "Commercial Town",
  "pincode_prefix": "751"
}
```

### Adding New Business Categories
Edit `config/categories.json`:
```json
{
  "id": "organic_farming",
  "name": "Organic Farming & Agro Products",
  "keywords": ["Organic", "Agro", "Farming", "Seeds"]
}
```

### Adding a New Source Adapter
Subclass `BaseSourceAdapter` in `backend/app/adapters/`:
```python
from app.adapters.base import BaseSourceAdapter

class IndiaMARTAdapter(BaseSourceAdapter):
    def __init__(self):
        super().__init__(name="indiamart")

    async def collect(self, city, category, max_scrolls, on_listing_collected, ...):
        # Implementation
        pass
```

---

## Running Automated Tests
```powershell
cd backend
.\.venv\Scripts\pytest.exe -v tests
```
All 15 unit and integration tests verify phone normalization, column detection, 3-tier deduplication, Excel generation, and full mock pipeline execution.
