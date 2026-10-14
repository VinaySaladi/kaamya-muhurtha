"""
Place lookup: built-in gazetteer of Indian (and common NRI) cities, optional
online geocoding (OpenStreetMap Nominatim, off by default), timezone detection.
"""
from __future__ import annotations

import os
import unicodedata
from dataclasses import dataclass
from functools import lru_cache

import httpx

from .astro.panchang import Place

# name: (lat, lon, tz, region)   region: telugu | marathi | north | south_other | intl
_IN = "Asia/Kolkata"
CITIES: dict[str, tuple[float, float, str, str]] = {
    # Telangana / Andhra Pradesh
    "hyderabad": (17.3850, 78.4867, _IN, "telugu"), "secunderabad": (17.4399, 78.4983, _IN, "telugu"),
    "warangal": (17.9689, 79.5941, _IN, "telugu"), "karimnagar": (18.4386, 79.1288, _IN, "telugu"),
    "nizamabad": (18.6725, 78.0941, _IN, "telugu"), "khammam": (17.2473, 80.1514, _IN, "telugu"),
    "nalgonda": (17.0575, 79.2671, _IN, "telugu"), "mahbubnagar": (16.7488, 77.9855, _IN, "telugu"),
    "adilabad": (19.6641, 78.5320, _IN, "telugu"), "siddipet": (18.1018, 78.8520, _IN, "telugu"),
    "vijayawada": (16.5062, 80.6480, _IN, "telugu"), "visakhapatnam": (17.6868, 83.2185, _IN, "telugu"),
    "vizag": (17.6868, 83.2185, _IN, "telugu"), "guntur": (16.3067, 80.4365, _IN, "telugu"),
    "tirupati": (13.6288, 79.4192, _IN, "telugu"), "nellore": (14.4426, 79.9865, _IN, "telugu"),
    "kurnool": (15.8281, 78.0373, _IN, "telugu"), "rajahmundry": (17.0005, 81.8040, _IN, "telugu"),
    "rajamahendravaram": (17.0005, 81.8040, _IN, "telugu"), "kakinada": (16.9891, 82.2475, _IN, "telugu"),
    "anantapur": (14.6819, 77.6006, _IN, "telugu"), "kadapa": (14.4673, 78.8242, _IN, "telugu"),
    "eluru": (16.7107, 81.0952, _IN, "telugu"), "ongole": (15.5057, 80.0499, _IN, "telugu"),
    "srikakulam": (18.2949, 83.8938, _IN, "telugu"), "vizianagaram": (18.1067, 83.3956, _IN, "telugu"),
    "amaravati": (16.5131, 80.5165, _IN, "telugu"), "bhadrachalam": (17.6688, 80.8936, _IN, "telugu"),
    # Maharashtra / Goa
    "mumbai": (19.0760, 72.8777, _IN, "marathi"), "bombay": (19.0760, 72.8777, _IN, "marathi"),
    "thane": (19.2183, 72.9781, _IN, "marathi"), "navi mumbai": (19.0330, 73.0297, _IN, "marathi"),
    "pune": (18.5204, 73.8567, _IN, "marathi"), "nagpur": (21.1458, 79.0882, _IN, "marathi"),
    "nashik": (19.9975, 73.7898, _IN, "marathi"), "aurangabad": (19.8762, 75.3433, _IN, "marathi"),
    "chhatrapati sambhajinagar": (19.8762, 75.3433, _IN, "marathi"), "solapur": (17.6599, 75.9064, _IN, "marathi"),
    "kolhapur": (16.7050, 74.2433, _IN, "marathi"), "amravati": (20.9374, 77.7796, _IN, "marathi"),
    "nanded": (19.1383, 77.3210, _IN, "marathi"), "sangli": (16.8524, 74.5815, _IN, "marathi"),
    "latur": (18.4088, 76.5604, _IN, "marathi"), "ahmednagar": (19.0948, 74.7480, _IN, "marathi"),
    "kalyan": (19.2403, 73.1305, _IN, "marathi"), "vasai": (19.3919, 72.8397, _IN, "marathi"),
    "satara": (17.6805, 74.0183, _IN, "marathi"), "ratnagiri": (16.9902, 73.3120, _IN, "marathi"),
    "panaji": (15.4909, 73.8278, _IN, "marathi"), "goa": (15.4909, 73.8278, _IN, "marathi"),
    # Other South
    "bengaluru": (12.9716, 77.5946, _IN, "south_other"), "bangalore": (12.9716, 77.5946, _IN, "south_other"),
    "chennai": (13.0827, 80.2707, _IN, "south_other"), "mysuru": (12.2958, 76.6394, _IN, "south_other"),
    "mysore": (12.2958, 76.6394, _IN, "south_other"), "coimbatore": (11.0168, 76.9558, _IN, "south_other"),
    "madurai": (9.9252, 78.1198, _IN, "south_other"), "kochi": (9.9312, 76.2673, _IN, "south_other"),
    "thiruvananthapuram": (8.5241, 76.9366, _IN, "south_other"), "mangaluru": (12.9141, 74.8560, _IN, "south_other"),
    "hubli": (15.3647, 75.1240, _IN, "south_other"), "belagavi": (15.8497, 74.4977, _IN, "marathi"),
    # North / East / West
    "delhi": (28.6139, 77.2090, _IN, "north"), "new delhi": (28.6139, 77.2090, _IN, "north"),
    "noida": (28.5355, 77.3910, _IN, "north"), "gurugram": (28.4595, 77.0266, _IN, "north"),
    "gurgaon": (28.4595, 77.0266, _IN, "north"), "jaipur": (26.9124, 75.7873, _IN, "north"),
    "lucknow": (26.8467, 80.9462, _IN, "north"), "kanpur": (26.4499, 80.3319, _IN, "north"),
    "varanasi": (25.3176, 82.9739, _IN, "north"), "prayagraj": (25.4358, 81.8463, _IN, "north"),
    "allahabad": (25.4358, 81.8463, _IN, "north"), "agra": (27.1767, 78.0081, _IN, "north"),
    "patna": (25.5941, 85.1376, _IN, "north"), "bhopal": (23.2599, 77.4126, _IN, "north"),
    "indore": (22.7196, 75.8577, _IN, "north"), "chandigarh": (30.7333, 76.7794, _IN, "north"),
    "dehradun": (30.3165, 78.0322, _IN, "north"), "haridwar": (29.9457, 78.1642, _IN, "north"),
    "ayodhya": (26.7922, 82.1998, _IN, "north"), "mathura": (27.4924, 77.6737, _IN, "north"),
    "raipur": (21.2514, 81.6296, _IN, "north"), "ranchi": (23.3441, 85.3096, _IN, "north"),
    "ahmedabad": (23.0225, 72.5714, _IN, "north"), "surat": (21.1702, 72.8311, _IN, "north"),
    "vadodara": (22.3072, 73.1812, _IN, "north"), "kolkata": (22.5726, 88.3639, _IN, "north"),
    "bhubaneswar": (20.2961, 85.8245, _IN, "north"), "guwahati": (26.1445, 91.7362, _IN, "north"),
    # International (common NRI birthplaces / venues)
    "dubai": (25.2048, 55.2708, "Asia/Dubai", "intl"), "singapore": (1.3521, 103.8198, "Asia/Singapore", "intl"),
    "london": (51.5074, -0.1278, "Europe/London", "intl"), "new york": (40.7128, -74.0060, "America/New_York", "intl"),
    "new jersey": (40.0583, -74.4057, "America/New_York", "intl"), "chicago": (41.8781, -87.6298, "America/Chicago", "intl"),
    "dallas": (32.7767, -96.7970, "America/Chicago", "intl"), "houston": (29.7604, -95.3698, "America/Chicago", "intl"),
    "san francisco": (37.7749, -122.4194, "America/Los_Angeles", "intl"),
    "san jose": (37.3382, -121.8863, "America/Los_Angeles", "intl"), "seattle": (47.6062, -122.3321, "America/Los_Angeles", "intl"),
    "atlanta": (33.7490, -84.3880, "America/New_York", "intl"), "toronto": (43.6532, -79.3832, "America/Toronto", "intl"),
    "sydney": (-33.8688, 151.2093, "Australia/Sydney", "intl"), "melbourne": (-37.8136, 144.9631, "Australia/Melbourne", "intl"),
}

STATE_REGION = {
    "telangana": "telugu", "andhra pradesh": "telugu", "maharashtra": "marathi", "goa": "marathi",
    "karnataka": "south_other", "tamil nadu": "south_other", "kerala": "south_other",
}


@dataclass
class ResolvedPlace:
    place: Place
    region: str
    source: str          # gazetteer | geocoder | coordinates
    display: str


def _key(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "").lower().strip()
    for junk in (",", ".", " india", " city", " district"):
        s = s.replace(junk, " ")
    return " ".join(s.split())


def _tz_for(lat: float, lon: float) -> str:
    try:
        from timezonefinder import TimezoneFinder
        return _tzf().timezone_at(lat=lat, lng=lon) or _IN
    except Exception:
        return _IN


@lru_cache(maxsize=1)
def _tzf():
    from timezonefinder import TimezoneFinder
    return TimezoneFinder()


def region_for_coords(lat: float, lon: float, tz: str) -> str:
    if tz != _IN:
        return "intl"
    # nearest gazetteer city decides the region
    best, bd = "telugu", 1e9
    for (clat, clon, ctz, reg) in CITIES.values():
        if ctz != _IN:
            continue
        d = (clat - lat) ** 2 + (clon - lon) ** 2
        if d < bd:
            best, bd = reg, d
    return best


def resolve(query: str | None = None, lat: float | None = None, lon: float | None = None,
            tz: str | None = None) -> list[ResolvedPlace]:
    """Return candidate places (best first). Empty list = not found."""
    if lat is not None and lon is not None:
        tz = tz or _tz_for(lat, lon)
        name = query or f"{lat:.4f}, {lon:.4f}"
        return [ResolvedPlace(Place(lat, lon, tz, name), region_for_coords(lat, lon, tz), "coordinates", name)]
    k = _key(query or "")
    if not k:
        return []
    if k in CITIES:
        la, lo, z, r = CITIES[k]
        return [ResolvedPlace(Place(la, lo, z, k.title()), r, "gazetteer", k.title())]
    hits = [c for c in CITIES if c in k or k in c]
    out = []
    for c in hits[:5]:
        la, lo, z, r = CITIES[c]
        out.append(ResolvedPlace(Place(la, lo, z, c.title()), r, "gazetteer", c.title()))
    if out:
        return out
    if os.getenv("KAAMYA_GEOCODER", "off").lower() == "nominatim":
        return _nominatim(query or "")
    return []


def _nominatim(q: str) -> list[ResolvedPlace]:
    ua = os.getenv("KAAMYA_GEOCODER_UA", "kaamya-muhurtha/1.0 (contact@thevaidikgroup.com)")
    try:
        r = httpx.get("https://nominatim.openstreetmap.org/search",
                      params={"q": q, "format": "json", "limit": 3, "addressdetails": 1},
                      headers={"User-Agent": ua}, timeout=8.0)
        r.raise_for_status()
    except Exception:
        return []
    out = []
    for item in r.json():
        la, lo = float(item["lat"]), float(item["lon"])
        z = _tz_for(la, lo)
        state = (item.get("address", {}).get("state") or "").lower()
        reg = STATE_REGION.get(state) or region_for_coords(la, lo, z)
        out.append(ResolvedPlace(Place(la, lo, z, item.get("display_name", q)[:80]), reg, "geocoder",
                                 item.get("display_name", q)))
    return out
