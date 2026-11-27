import asyncio
import random
from datetime import datetime
from typing import List, Dict, Any, Callable, Awaitable, Tuple
from app.adapters.base import BaseSourceAdapter
from app.services.normalizer import clean_phone_number, title_case_name

CITY_LOCALITIES = {
    "bhubaneswar": ["Saheed Nagar", "Jayadev Vihar", "Patia", "Nayapalli", "Khandagiri", "Chandrasekharpur", "Infocity", "Rasulgarh"],
    "cuttack": ["CDA Sector 9", "Badambadi", "Buxi Bazar", "Link Road", "Choudhury Bazar", "College Square", "Mangalabag"],
    "puri": ["VIP Road", "Grand Road (Bada Danda)", "Sea Beach", "Chakratirtha Road", "Swargadwar"],
    "rourkela": ["Udit Nagar", "Civil Township", "Sector 19", "Koel Nagar", "Panposh"],
    "berhampur": ["Gandhi Nagar", "Gosaninuagaon", "Aska Road", "Kamapalli", "Courtpeta"],
    "sambalpur": ["Budharaja", "Ainthapali", "Dhanupali", "Khetrajpur"],
    "mumbai": ["Andheri West", "Bandra", "Powai", "Lower Parel", "Malad"],
    "bengaluru": ["Indiranagar", "Koramangala", "HSR Layout", "Whitefield", "Jayanagar"],
    "new delhi": ["Connaught Place", "Saket", "Lajpat Nagar", "Karol Bagh", "Dwarka"],
    "hyderabad": ["Banjara Hills", "Madhapur", "Gachibowli", "Jubilee Hills", "Secunderabad"],
    "kolkata": ["Salt Lake", "Park Street", "New Town", "Ballygunge", "Gariahat"],
    "pune": ["Kothrud", "Viman Nagar", "Baner", "Hinjewadi", "Koregaon Park"],
}

DEFAULT_LOCALITIES = ["Main Road", "Station Square", "Gandhi Chowk", "Market Complex", "Civil Lines"]

NAME_PREFIXES = [
    "Utkal", "Kalinga", "Konark", "Mahanadi", "Shree", "Royal", "Apex", "Zenith",
    "Prime", "Sunrise", "Sai", "Balaji", "Pinnacle", "Arogya", "Navaratna", "Swastik",
    "Bharat", "Metro", "Signature", "CarePlus", "Elite", "Heritage"
]

INDIAN_MOBILE_SERIES = ["9861", "9437", "7008", "8249", "9937", "6370", "8917", "9820", "9811", "9845"]


class MockOdishaAdapter(BaseSourceAdapter):
    """
    High-fidelity Demo Adapter supporting all Indian states & cities.
    Generates realistic commercial listings with websites, social-only links,
    emails, ratings, and review distributions so all Smart Filters work out of the box.
    """

    def __init__(self):
        super().__init__(name="mock")
        self._closed = False

    def capabilities(self) -> Dict[str, bool]:
        return {
            "has_website": True,
            "mobile": True,
            "email": True,
            "rating": True,
            "reviews": True,
            "verified": True,
            "social_only": True,
            "exclude_chains": True,
        }

    async def collect(
        self,
        city: str,
        category: str,
        max_scrolls: int,
        on_listing_collected: Callable[[Dict[str, Any]], Awaitable[None]],
        on_progress_update: Callable[[str, str], Awaitable[None]],
        check_pause_cancel: Callable[[], Awaitable[Tuple[bool, bool]]],
        wait_for_resume: Callable[[], Awaitable[None]],
        state: str = "Odisha",
    ) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        city_slug = city.lower().strip()
        localities = CITY_LOCALITIES.get(city_slug, DEFAULT_LOCALITIES)

        num_listings = random.randint(7, 12)

        await on_progress_update(
            "Searching",
            f"Querying business directory in {city}, {state} for {category}..."
        )
        await asyncio.sleep(0.25)

        short_cat = category.split("&")[0].strip()

        for i in range(1, num_listings + 1):
            is_paused, is_cancelled = await check_pause_cancel()
            if is_cancelled:
                break
            if is_paused:
                await wait_for_resume()

            prefix = random.choice(NAME_PREFIXES)
            locality = random.choice(localities)
            suffix = random.choice(["Services", "Solutions", "Centre", "Hub", "Associates", "Care"])
            business_name = f"{prefix} {short_cat} {suffix}"

            series = random.choice(INDIAN_MOBILE_SERIES)
            tail = f"{random.randint(100000, 999999)}"
            phone_clean, phone_fmt = clean_phone_number(f"+91 {series}{tail}")

            alt_phone = None
            if random.random() > 0.65:
                _, alt_phone = clean_phone_number(f"{random.choice(INDIAN_MOBILE_SERIES)}{random.randint(100000, 999999)}")

            pincode = f"{random.randint(11, 85)}{random.randint(1000, 9999)}"
            if state.lower() == "odisha":
                pincode = f"75{random.randint(1000, 9999)}"

            rating = f"{random.choice([3.1, 3.4, 3.8, 4.0, 4.2, 4.4, 4.6, 4.8]):.1f}"
            reviews = str(random.choice([5, 11, 18, 26, 42, 75, 130, 290]))

            slug_name = business_name.lower().replace(" ", "-").replace("&", "and")
            slug_city = city.lower().replace(" ", "-")

            # ~42% have a website, ~58% do NOT have a website (great for Website Design Pitch!)
            has_site = random.random() < 0.42
            website = f"https://www.{slug_name}-{slug_city}.in" if has_site else None
            social_url = f"https://instagram.com/{slug_name.replace('-', '')}" if (not has_site and random.random() < 0.45) else None
            email = f"contact@{slug_name}.in" if (has_site or random.random() < 0.3) else None

            listing = {
                "business_name": title_case_name(business_name),
                "category": category,
                "phone": phone_fmt,
                "phone_clean": phone_clean,
                "alt_phone": alt_phone,
                "email": email,
                "address": f"Plot No. {random.randint(12, 850)}, Near {locality} Square, {locality}, {city}, {state}",
                "area": locality,
                "city": city,
                "state": state,
                "district": city,
                "pincode": pincode,
                "rating": rating,
                "review_count": reviews,
                "website": website,
                "social_url": social_url,
                "is_verified_listing": random.random() < 0.55,
                "is_chain": False,
                "listing_url": f"https://www.justdial.com/{slug_city}/{slug_name}",
                "source": "LeadHarvest Demo Engine",
                "collected_at": datetime.utcnow(),
            }

            results.append(listing)
            await on_listing_collected(listing)
            await asyncio.sleep(0.08)

        return results

    async def close(self):
        self._closed = True
