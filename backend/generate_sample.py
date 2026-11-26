import asyncio
from datetime import datetime
from pathlib import Path
from app.adapters.mock_adapter import MockOdishaAdapter
from app.services.deduper import DeduplicationEngine
from app.services.exporter import generate_leads_excel

async def generate_demo_excel():
    adapter = MockOdishaAdapter()
    deduper = DeduplicationEngine()
    
    cities = ["Bhubaneswar", "Cuttack", "Puri", "Rourkela", "Berhampur (Brahmapur)"]
    categories = ["Restaurants & Cafes", "Hotels & Resorts", "Hospitals & Clinics", "Real Estate Agents & Builders"]
    
    collected_leads = []
    skipped_duplicates = []
    
    for city in cities:
        for cat in categories:
            async def on_listing(listing):
                is_dupe, rule, src = deduper.check_duplicate(listing)
                if is_dupe:
                    listing["is_duplicate"] = True
                    listing["duplicate_rule"] = rule
                    listing["duplicate_source"] = src
                    skipped_duplicates.append(listing)
                else:
                    listing["is_duplicate"] = False
                    collected_leads.append(listing)
                    deduper.register_new_lead(listing, source_label="Sample Run")

            async def on_progress(s, d):
                pass
            async def check_pc():
                return False, False
            async def wait_res():
                pass

            await adapter.collect(
                city=city,
                category=cat,
                max_scrolls=2,
                on_listing_collected=on_listing,
                on_progress_update=on_progress,
                check_pause_cancel=check_pc,
                wait_for_resume=wait_res
            )
            
    out_dir = Path(__file__).resolve().parent.parent / "docs"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "LeadHarvest_Odisha_Sample_Output.xlsx"
    
    summary_meta = {
        "run_timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "duration": "1m 45s",
        "cities": cities,
        "categories": categories,
        "total_found": len(collected_leads) + len(skipped_duplicates),
        "adapter": "Odisha High-Precision Demo Engine"
    }
    
    generate_leads_excel(collected_leads, skipped_duplicates, summary_meta, out_file)
    print(f"Generated sample Excel file at: {out_file} with {len(collected_leads)} leads and {len(skipped_duplicates)} duplicates skipped.")

if __name__ == "__main__":
    asyncio.run(generate_demo_excel())
