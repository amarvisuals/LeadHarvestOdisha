import asyncio
import random
from datetime import datetime
from typing import List, Dict, Any, Callable, Awaitable, Tuple
from app.adapters.base import BaseSourceAdapter
from app.services.normalizer import clean_phone_number, title_case_name

# Authentic Odisha Localities by City
ODISHA_LOCALITIES = {
    "bhubaneswar": ["Saheed Nagar", "Jayadev Vihar", "Patia", "Nayapalli", "Khandagiri", "Chandrasekharpur", "Infocity", "Rasulgarh"],
    "cuttack": ["CDA Sector 9", "Badambadi", "Buxi Bazar", "Link Road", "Choudhury Bazar", "College Square", "Mangalabag"],
    "puri": ["VIP Road", "Grand Road (Bada Danda)", "Sea Beach", "Chakratirtha Road", "Atharnala", "Swargadwar"],
    "rourkela": ["Udit Nagar", "Civil Township", "Sector 19", "Koel Nagar", "Panposh", "Chhend Colony"],
    "berhampur": ["Gandhi Nagar", "Gosaninuagaon", "Aska Road", "Kamapalli", "Courtpeta", "Bada Bazar"],
    "sambalpur": ["Budharaja", "Ainthapali", "Dhanupali", "Khetrajpur", "Fatak", "Brooks Hill"],
    "balasore": ["Sahadevkhunta", "Motiganj", "Cinema Bazar", "Station Road", "Remuna Golei"],
    "bhadrak": ["Charampa", "Bypass Road", "Puruna Bazar", "Banta Road"],
    "jharsuguda": ["Sarbahal", "Mangal Bazar", "Beherapat", "Kalimandir Road"],
    "angul": ["Amalapada", "Hakimpada", "Turang", "Mishrapada"],
    "jeypore": ["M.G. Road", "Brahmin Street", "Parabeda", "Bank Colony"]
}

DEFAULT_LOCALITIES = ["Main Road", "Station Square", "Gandhi Chowk", "Market Complex", "College Road"]

# Authentic Business Name Stems for Odisha
NAME_PREFIXES = [
    "Utkal", "Kalinga", "Konark", "Mahanadi", "Lord Jagannath", "Bhubaneswar", "Cuttack",
    "Odisha", "Maa Tarini", "Chilika", "Barabati", "Biju", "East Coast", "Heritage", "Royal",
    "Apex", "Zenith", "Prime", "Sunrise", "Shree", "Sai", "Balaji", "Pinnacle"
]

ODISHA_MOBILE_SERIES = ["9861", "9437", "7008", "8249", "9937", "6370", "8917", "7894", "9668"]

class MockOdishaAdapter(BaseSourceAdapter):
    """
    High-fidelity Mock Adapter for instant offline demos, testing, and continuous validation.
    Generates realistic, nuanced Odisha commercial listings with accurate geographic details.
    """

    def __init__(self):
        super().__init__(name="mock")
        self._closed = False

    async def collect(
        self,
        city: str,
        category: str,
        max_scrolls: int,
        on_listing_collected: Callable[[Dict[str, Any]], Awaitable[None]],
        on_progress_update: Callable[[str, str], Awaitable[None]],
        check_pause_cancel: Callable[[], Awaitable[Tuple[bool, bool]]],
        wait_for_resume: Callable[[], Awaitable[None]]
    ) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        city_slug = city.lower().replace(" ", "_")
        localities = ODISHA_LOCALITIES.get(city_slug, DEFAULT_LOCALITIES)

        # Generate between 6 and 14 authentic listings per city & category
        num_listings = random.randint(6, 12)
        
        await on_progress_update(
            "Searching",
            f"Querying business directory in {city} for {category}..."
        )
        await asyncio.sleep(0.4)

        for i in range(1, num_listings + 1):
            # Check pause / cancel
            is_paused, is_cancelled = await check_pause_cancel()
            if is_cancelled:
                break
            if is_paused:
                await wait_for_resume()

            prefix = random.choice(NAME_PREFIXES)
            locality = random.choice(localities)
            business_name = f"{prefix} {category.split('&')[0].strip()} Services"
            if random.random() > 0.4:
                business_name = f"{prefix} {category.split('&')[0].strip()} & Solutions"

            # Authentic phone generation
            series = random.choice(ODISHA_MOBILE_SERIES)
            tail = f"{random.randint(100000, 999999)}"
            phone_raw = f"+91 {series}{tail}"
            phone_clean, phone_fmt = clean_phone_number(phone_raw)

            alt_phone = None
            if random.random() > 0.6:
                alt_series = random.choice(ODISHA_MOBILE_SERIES)
                alt_tail = f"{random.randint(100000, 999999)}"
                _, alt_phone = clean_phone_number(f"{alt_series}{alt_tail}")

            pincode = f"75{random.randint(1000, 9999)}"
            rating = f"{random.choice([4.1, 4.3, 4.5, 4.7, 4.8, 4.9]):.1f}"
            reviews = str(random.randint(18, 480))
            
            slug_name = business_name.lower().replace(" ", "-").replace("&", "and")
            slug_city = city.lower().replace(" ", "-")
            
            listing = {
                "business_name": title_case_name(business_name),
                "category": category,
                "phone": phone_fmt,
                "phone_clean": phone_clean,
                "alt_phone": alt_phone,
                "address": f"Plot No. {random.randint(12, 850)}, Near {locality} Square, {locality}, {city}",
                "area": locality,
                "city": city,
                "district": city,
                "pincode": pincode,
                "rating": rating,
                "review_count": reviews,
                "website": f"https://www.{slug_name}-{slug_city}.in" if random.random() > 0.5 else None,
                "listing_url": f"https://www.justdial.com/{slug_city}/{slug_name}",
                "source": "MockOdishaEngine",
                "collected_at": datetime.utcnow()
            }

            results.append(listing)
            await on_listing_collected(listing)
            
            # Subtle realistic pacing simulation
            await asyncio.sleep(0.15)

        return results

    async def close(self):
        self._closed = True
