from app.services.lead_filters import (
    enrich_lead_metadata,
    matches_smart_filters,
    detect_chains_across_leads,
)


def test_opportunity_score_and_tags():
    # High opportunity: No website (+40), Mobile (+20), Low reviews (+15), Good rating (+15), Address+Pin (+10) = 100
    hot_lead = enrich_lead_metadata({
        "business_name": "Cuttack Smile Dental Clinic",
        "phone_clean": "9861012345",
        "website": None,
        "rating": "4.3",
        "review_count": "18",
        "address": "CDA Sector 9, Cuttack",
        "pincode": "753014",
    })
    assert hot_lead["has_website"] is False
    assert hot_lead["mobile_available"] is True
    assert hot_lead["opportunity_score"] == 100
    assert hot_lead["lead_tag"] == "Hot Website Pitch"
    assert hot_lead["whatsapp_link"] == "https://wa.me/919861012345"

    # Has website (+0), Mobile (+20), Low reviews (+15), Good rating (+15), Address+Pin (+10) = 60
    seo_lead = enrich_lead_metadata({
        "business_name": "Apex Builders",
        "phone_clean": "9437012345",
        "website": "https://apexbuilders.in",
        "rating": "4.2",
        "review_count": "12",
        "address": "Patia, Bhubaneswar",
        "pincode": "751024",
    })
    assert seo_lead["has_website"] is True
    assert seo_lead["opportunity_score"] == 60
    assert seo_lead["lead_tag"] == "SEO / Ads Pitch"


def test_smart_filters_no_website_and_score():
    no_site = enrich_lead_metadata({
        "business_name": "Local Clinic",
        "phone_clean": "7008011223",
        "website": None,
        "rating": "4.1",
        "review_count": "10",
        "address": "Saheed Nagar",
        "pincode": "751007",
    })
    with_site = enrich_lead_metadata({
        "business_name": "Corporate Clinic",
        "phone_clean": "7008099887",
        "website": "https://corpclinic.in",
        "rating": "4.5",
        "review_count": "200",
        "address": "Jayadev Vihar",
        "pincode": "751013",
    })

    filters = {"no_website": True, "mobile_only": True, "min_opportunity_score": 80}
    assert matches_smart_filters(no_site, filters)[0] is True
    assert matches_smart_filters(with_site, filters)[0] is False


def test_exclude_chains_heuristic():
    leads = [
        {"business_name": "Apollo Pharmacy", "city": "Bhubaneswar"},
        {"business_name": "Apollo Pharmacy", "city": "Cuttack"},
        {"business_name": "Apollo Pharmacy", "city": "Puri"},
        {"business_name": "Apollo Pharmacy", "city": "Rourkela"},
        {"business_name": "Kalinga Medicos", "city": "Bhubaneswar"},
    ]
    detect_chains_across_leads(leads, min_cities=4)
    assert leads[0]["is_chain"] is True
    assert leads[4].get("is_chain", False) is False
