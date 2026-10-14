"""Panchang names in English (transliterated Sanskrit), Telugu, Hindi and Marathi."""
from __future__ import annotations

LANGS = ("en", "te", "hi", "mr")

NAKSHATRA = {
    "en": ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya",
           "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati",
           "Vishakha", "Anuradha", "Jyeshtha", "Moola", "Purva Ashadha", "Uttara Ashadha", "Shravana",
           "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"],
    "te": ["అశ్విని", "భరణి", "కృత్తిక", "రోహిణి", "మృగశిర", "ఆర్ద్ర", "పునర్వసు", "పుష్యమి",
           "ఆశ్లేష", "మఖ", "పుబ్బ", "ఉత్తర", "హస్త", "చిత్త", "స్వాతి",
           "విశాఖ", "అనూరాధ", "జ్యేష్ఠ", "మూల", "పూర్వాషాఢ", "ఉత్తరాషాఢ", "శ్రవణం",
           "ధనిష్ఠ", "శతభిషం", "పూర్వాభాద్ర", "ఉత్తరాభాద్ర", "రేవతి"],
    "hi": ["अश्विनी", "भरणी", "कृत्तिका", "रोहिणी", "मृगशिरा", "आर्द्रा", "पुनर्वसु", "पुष्य",
           "आश्लेषा", "मघा", "पूर्वा फाल्गुनी", "उत्तरा फाल्गुनी", "हस्त", "चित्रा", "स्वाती",
           "विशाखा", "अनुराधा", "ज्येष्ठा", "मूल", "पूर्वाषाढ़ा", "उत्तराषाढ़ा", "श्रवण",
           "धनिष्ठा", "शतभिषा", "पूर्वा भाद्रपद", "उत्तरा भाद्रपद", "रेवती"],
}
NAKSHATRA["mr"] = [n.replace("ढ़", "ढ") for n in NAKSHATRA["hi"]]

TITHI = {
    "en": ["Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami", "Shashthi", "Saptami", "Ashtami",
           "Navami", "Dashami", "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Purnima", "Amavasya"],
    "te": ["పాడ్యమి", "విదియ", "తదియ", "చవితి", "పంచమి", "షష్ఠి", "సప్తమి", "అష్టమి",
           "నవమి", "దశమి", "ఏకాదశి", "ద్వాదశి", "త్రయోదశి", "చతుర్దశి", "పౌర్ణమి", "అమావాస్య"],
    "hi": ["प्रतिपदा", "द्वितीया", "तृतीया", "चतुर्थी", "पंचमी", "षष्ठी", "सप्तमी", "अष्टमी",
           "नवमी", "दशमी", "एकादशी", "द्वादशी", "त्रयोदशी", "चतुर्दशी", "पूर्णिमा", "अमावस्या"],
    "mr": ["प्रतिपदा", "द्वितीया", "तृतीया", "चतुर्थी", "पंचमी", "षष्ठी", "सप्तमी", "अष्टमी",
           "नवमी", "दशमी", "एकादशी", "द्वादशी", "त्रयोदशी", "चतुर्दशी", "पौर्णिमा", "अमावस्या"],
}

PAKSHA = {
    "en": ["Shukla Paksha", "Krishna Paksha"],
    "te": ["శుక్ల పక్షం", "బహుళ పక్షం"],
    "hi": ["शुक्ल पक्ष", "कृष्ण पक्ष"],
    "mr": ["शुक्ल पक्ष", "कृष्ण पक्ष"],
}

VARA = {  # 0 = Sunday
    "en": ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
    "te": ["ఆదివారం", "సోమవారం", "మంగళవారం", "బుధవారం", "గురువారం", "శుక్రవారం", "శనివారం"],
    "hi": ["रविवार", "सोमवार", "मंगलवार", "बुधवार", "गुरुवार", "शुक्रवार", "शनिवार"],
    "mr": ["रविवार", "सोमवार", "मंगळवार", "बुधवार", "गुरुवार", "शुक्रवार", "शनिवार"],
}

RASHI = {
    "en": ["Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya", "Tula", "Vrischika",
           "Dhanu", "Makara", "Kumbha", "Meena"],
    "te": ["మేషం", "వృషభం", "మిథునం", "కర్కాటకం", "సింహం", "కన్య", "తుల", "వృశ్చికం",
           "ధనుస్సు", "మకరం", "కుంభం", "మీనం"],
    "hi": ["मेष", "वृषभ", "मिथुन", "कर्क", "सिंह", "कन्या", "तुला", "वृश्चिक",
           "धनु", "मकर", "कुंभ", "मीन"],
    "mr": ["मेष", "वृषभ", "मिथुन", "कर्क", "सिंह", "कन्या", "तूळ", "वृश्चिक",
           "धनु", "मकर", "कुंभ", "मीन"],
}

MASA = {  # amanta lunar months, 0 = Chaitra
    "en": ["Chaitra", "Vaishakha", "Jyeshtha", "Ashadha", "Shravana", "Bhadrapada", "Ashwayuja",
           "Kartika", "Margashira", "Pushya", "Magha", "Phalguna"],
    "te": ["చైత్రం", "వైశాఖం", "జ్యేష్ఠం", "ఆషాఢం", "శ్రావణం", "భాద్రపదం", "ఆశ్వయుజం",
           "కార్తీకం", "మార్గశిరం", "పుష్యం", "మాఘం", "ఫాల్గుణం"],
    "hi": ["चैत्र", "वैशाख", "ज्येष्ठ", "आषाढ़", "श्रावण", "भाद्रपद", "आश्विन",
           "कार्तिक", "मार्गशीर्ष", "पौष", "माघ", "फाल्गुन"],
    "mr": ["चैत्र", "वैशाख", "ज्येष्ठ", "आषाढ", "श्रावण", "भाद्रपद", "आश्विन",
           "कार्तिक", "मार्गशीर्ष", "पौष", "माघ", "फाल्गुन"],
}

YOGA_EN = ["Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana", "Atiganda", "Sukarma", "Dhriti",
           "Shoola", "Ganda", "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra", "Siddhi",
           "Vyatipata", "Variyan", "Parigha", "Shiva", "Siddha", "Sadhya", "Shubha", "Shukla",
           "Brahma", "Indra", "Vaidhriti"]

KARANA_EN = ["Kimstughna", "Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Vishti",
             "Shakuni", "Chatushpada", "Naga"]

SAMVATSARA_EN = [
    "Prabhava", "Vibhava", "Shukla", "Pramoda", "Prajapati", "Angirasa", "Shrimukha", "Bhava", "Yuva",
    "Dhatu", "Ishvara", "Bahudhanya", "Pramathi", "Vikrama", "Vrisha", "Chitrabhanu", "Svabhanu",
    "Tarana", "Parthiva", "Vyaya", "Sarvajit", "Sarvadhari", "Virodhi", "Vikriti", "Khara", "Nandana",
    "Vijaya", "Jaya", "Manmatha", "Durmukhi", "Hevilambi", "Vilambi", "Vikari", "Sharvari", "Plava",
    "Shubhakrit", "Shobhakrit", "Krodhi", "Vishvavasu", "Parabhava", "Plavanga", "Kilaka", "Saumya",
    "Sadharana", "Virodhikrit", "Paridhavi", "Pramadi", "Ananda", "Rakshasa", "Nala", "Pingala",
    "Kalayukti", "Siddharthi", "Raudri", "Durmati", "Dundubhi", "Rudhirodgari", "Raktakshi",
    "Krodhana", "Akshaya",
]
assert len(SAMVATSARA_EN) == 60

ADHIKA = {"en": "Adhika", "te": "అధిక", "hi": "अधिक", "mr": "अधिक"}

TARA_EN = ["Janma", "Sampat", "Vipat", "Kshema", "Pratyak", "Sadhana", "Naidhana", "Mitra", "Parama Mitra"]

LAGNA_TYPE_EN = {0: "Chara (movable)", 1: "Sthira (fixed)", 2: "Dvisvabhava (dual)"}


def name(table: dict, idx: int, lang: str) -> str:
    lang = lang if lang in table else "en"
    return table[lang][idx]


def nak_index_from_name(s: str) -> int | None:
    """Accept English spellings (and common variants) or native script names."""
    if s is None:
        return None
    key = s.strip().lower().replace("-", " ").replace("  ", " ")
    aliases = {
        "aswini": 0, "ashvini": 0, "bharni": 1, "kritika": 2, "karthika": 2, "krithika": 2,
        "mrigasira": 4, "mrigashirsha": 4, "mrugasira": 4, "arudra": 5, "aardra": 5, "thiruvathirai": 5,
        "pushyami": 7, "pushya": 7, "pooyam": 7, "aslesha": 8, "ashlesha": 8, "makha": 9, "magam": 9,
        "pubba": 10, "purva phalguni": 10, "poorva phalguni": 10, "uttara": 11, "uttaram": 11,
        "uttara phalguni": 11, "chitta": 13, "chithra": 13, "swathi": 14, "swati": 14, "visakha": 15,
        "anuradha": 16, "anusham": 16, "jyeshta": 17, "jyestha": 17, "kettai": 17, "mula": 18, "moolam": 18,
        "purvashadha": 19, "poorvashada": 19, "purva ashadha": 19, "uttarashadha": 20, "uttarashada": 20,
        "sravana": 21, "shravanam": 21, "thiruvonam": 21, "dhanishtha": 22, "avittam": 22,
        "shatabhisham": 23, "satabhisha": 23, "sadhayam": 23, "purvabhadra": 24, "purva bhadra": 24,
        "poorvabhadra": 24, "uttarabhadra": 25, "uttara bhadra": 25, "revathi": 26,
    }
    if key in aliases:
        return aliases[key]
    for lang, names in NAKSHATRA.items():
        for i, n in enumerate(names):
            if n.lower() == key or n.lower().replace(" ", "") == key.replace(" ", ""):
                return i
    return None


def rashi_index_from_name(s: str) -> int | None:
    if s is None:
        return None
    key = s.strip().lower()
    western = ["aries", "taurus", "gemini", "cancer", "leo", "virgo", "libra", "scorpio",
               "sagittarius", "capricorn", "aquarius", "pisces"]
    aliases = {"vrushabha": 1, "vrishabham": 1, "mithunam": 2, "karkataka": 3, "karkatakam": 3, "kark": 3,
               "simham": 4, "singh": 4, "kanni": 5, "thula": 6, "tulam": 6, "vrischikam": 7, "vrishchika": 7,
               "dhanus": 8, "dhanussu": 8, "dhanur": 8, "makaram": 9, "kumbham": 10, "meenam": 11, "mesham": 0}
    if key in western:
        return western.index(key)
    if key in aliases:
        return aliases[key]
    for lang, names in RASHI.items():
        for i, n in enumerate(names):
            if n.lower() == key:
                return i
    return None
