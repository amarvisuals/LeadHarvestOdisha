# LeadHarvest Odisha – Architecture & System Design

## 1. System Overview
**LeadHarvest Odisha** is a specialized, production-grade business lead collection and deduplication system focused exclusively on Odisha, India. It enables non-technical business owners and sales teams to select locations and industries, skip historical leads, and receive clean, formatted 3-sheet Excel files with a single click.

```
┌────────────────────────────────────────────────────────┐
│                   Next.js 14 Frontend                  │
│  - 3-Step Wizard Layout (Locations, Categories, Dedupe)│
│  - Live Animated SVG Hourglass & Ring Loaders          │
│  - Server-Sent Events (SSE) Live Progress Subscriber   │
└───────────────────────────┬────────────────────────────┘
                            │ HTTP & SSE Streaming
┌───────────────────────────▼────────────────────────────┐
│                  FastAPI Backend Server                │
│  - REST Endpoints (/api/jobs, /api/uploads, /api/config)│
│  - Background Job Runner (AsyncIO Task Queue)          │
│  - SQLite (SQLAlchemy Async) Persistent Storage        │
└───────────────┬────────────────────────┬───────────────┘
                │                        │
┌───────────────▼──────────────┐ ┌───────▼──────────────┐
│   Pluggable Source Adapters  │ │ Deduplication Engine │
│ - MockOdishaAdapter (Instant)│ │ - Tier 1: Clean Phone│
│ - JustdialAdapter (Playwright│ │ - Tier 2: Name+City  │
│   Async, Concurrency Pool)   │ │ - Tier 3: RapidFuzz  │
└──────────────────────────────┘ └───────┬──────────────┘
                                         │
                         ┌───────────────▼──────────────┐
                         │      OpenPyXL Exporter       │
                         │ Sheet 1: Clean Leads         │
                         │ Sheet 2: Search Summary      │
                         │ Sheet 3: Skipped Duplicates  │
                         └──────────────────────────────┘
```

## 2. Pluggable Source Adapter Architecture
Lead sources are abstracted under `BaseSourceAdapter` (`app/adapters/base.py`):
```python
class BaseSourceAdapter(ABC):
    async def collect(
        self, city: str, category: str, max_scrolls: int,
        on_listing_collected: Callable,
        on_progress_update: Callable,
        check_pause_cancel: Callable,
        wait_for_resume: Callable
    ) -> List[Dict[str, Any]]: ...
```
- **MockOdishaAdapter**: High-fidelity offline data generator producing authentic Odisha listings (real telecom series `9861`, `9437`, `7008`; real pin prefixes `751`, `753`, `769`; authentic localities).
- **JustdialAdapter**: Realistic Playwright async scraper with honest pacing (2-5s random delays), concurrency capped to 1-2 pages, exponential backoff, and non-crashing page error recovery.

## 3. Three-Tier Deduplication Pipeline
All harvested records are evaluated against the persistent SQLite `known_records` table and intra-run leads in strict priority:
1. **Rule 1 (Normalized 10-Digit Phone Match)**:
   - Strips country prefix `+91`, leading `0`, punctuation, and spaces.
   - Validates Indian telecom series (`6`, `7`, `8`, `9`).
   - Discards generic toll-free/helplines.
2. **Rule 2 (Exact Business Name + City Match)**:
   - Case-insensitive, whitespace-trimmed, punctuation-sanitized comparison within the same city.
3. **Rule 3 (Fuzzy Token Sort Match)**:
   - RapidFuzz `token_sort_ratio >= 90` on composite `normalized_name + normalized_address` within the same city.

## 4. Resilience & Resumability
- Background jobs run in an asynchronous task queue.
- SQLite transactions update after every page batch.
- User can **Pause**, **Resume**, or **Cancel** (cancel flushes collected records immediately to Excel so partial work is never lost).
- CAPTCHA/bot challenges trigger an automated pause state with a user-friendly UI prompt rather than evading blocks.
