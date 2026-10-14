/* Kaamya Muhurtha engine - JavaScript port of the Python service (app/astro, app/rules, app/i18n, app/places).
   Same rules, same numbers. Runs in the browser (global Astronomy) or Node (require('astronomy-engine')). */
(function (root) {
  "use strict";
  const A = root.Astronomy || (typeof require !== "undefined" ? require("astronomy-engine") : null);
  const J2000_MS = Date.UTC(2000, 0, 1, 12, 0, 0);
  const NAK = 360 / 27;
  const norm = (x) => ((x % 360) + 360) % 360;
  const utToMs = (ut) => J2000_MS + ut * 86400000;
  const msToUt = (ms) => (ms - J2000_MS) / 86400000;
  const T = (ut) => new A.AstroTime(ut);
  const r5 = (x) => Math.round(x * 1e5) / 1e5;

  // ------------------------------------------------------------------ i18n
  const L = {
    NAKSHATRA: {
      en: ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Moola", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"],
      te: ["అశ్విని", "భరణి", "కృత్తిక", "రోహిణి", "మృగశిర", "ఆర్ద్ర", "పునర్వసు", "పుష్యమి", "ఆశ్లేష", "మఖ", "పుబ్బ", "ఉత్తర", "హస్త", "చిత్త", "స్వాతి", "విశాఖ", "అనూరాధ", "జ్యేష్ఠ", "మూల", "పూర్వాషాఢ", "ఉత్తరాషాఢ", "శ్రవణం", "ధనిష్ఠ", "శతభిషం", "పూర్వాభాద్ర", "ఉత్తరాభాద్ర", "రేవతి"],
      hi: ["अश्विनी", "भरणी", "कृत्तिका", "रोहिणी", "मृगशिरा", "आर्द्रा", "पुनर्वसु", "पुष्य", "आश्लेषा", "मघा", "पूर्वा फाल्गुनी", "उत्तरा फाल्गुनी", "हस्त", "चित्रा", "स्वाती", "विशाखा", "अनुराधा", "ज्येष्ठा", "मूल", "पूर्वाषाढ़ा", "उत्तराषाढ़ा", "श्रवण", "धनिष्ठा", "शतभिषा", "पूर्वा भाद्रपद", "उत्तरा भाद्रपद", "रेवती"],
    },
    TITHI: {
      en: ["Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami", "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami", "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Purnima", "Amavasya"],
      te: ["పాడ్యమి", "విదియ", "తదియ", "చవితి", "పంచమి", "షష్ఠి", "సప్తమి", "అష్టమి", "నవమి", "దశమి", "ఏకాదశి", "ద్వాదశి", "త్రయోదశి", "చతుర్దశి", "పౌర్ణమి", "అమావాస్య"],
      hi: ["प्रतिपदा", "द्वितीया", "तृतीया", "चतुर्थी", "पंचमी", "षष्ठी", "सप्तमी", "अष्टमी", "नवमी", "दशमी", "एकादशी", "द्वादशी", "त्रयोदशी", "चतुर्दशी", "पूर्णिमा", "अमावस्या"],
      mr: ["प्रतिपदा", "द्वितीया", "तृतीया", "चतुर्थी", "पंचमी", "षष्ठी", "सप्तमी", "अष्टमी", "नवमी", "दशमी", "एकादशी", "द्वादशी", "त्रयोदशी", "चतुर्दशी", "पौर्णिमा", "अमावस्या"],
    },
    PAKSHA: { en: ["Shukla Paksha", "Krishna Paksha"], te: ["శుక్ల పక్షం", "బహుళ పక్షం"], hi: ["शुक्ल पक्ष", "कृष्ण पक्ष"], mr: ["शुक्ल पक्ष", "कृष्ण पक्ष"] },
    VARA: {
      en: ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
      te: ["ఆదివారం", "సోమవారం", "మంగళవారం", "బుధవారం", "గురువారం", "శుక్రవారం", "శనివారం"],
      hi: ["रविवार", "सोमवार", "मंगलवार", "बुधवार", "गुरुवार", "शुक्रवार", "शनिवार"],
      mr: ["रविवार", "सोमवार", "मंगळवार", "बुधवार", "गुरुवार", "शुक्रवार", "शनिवार"],
    },
    RASHI: {
      en: ["Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya", "Tula", "Vrischika", "Dhanu", "Makara", "Kumbha", "Meena"],
      te: ["మేషం", "వృషభం", "మిథునం", "కర్కాటకం", "సింహం", "కన్య", "తుల", "వృశ్చికం", "ధనుస్సు", "మకరం", "కుంభం", "మీనం"],
      hi: ["मेष", "वृषभ", "मिथुन", "कर्क", "सिंह", "कन्या", "तुला", "वृश्चिक", "धनु", "मकर", "कुंभ", "मीन"],
      mr: ["मेष", "वृषभ", "मिथुन", "कर्क", "सिंह", "कन्या", "तूळ", "वृश्चिक", "धनु", "मकर", "कुंभ", "मीन"],
    },
    MASA: {
      en: ["Chaitra", "Vaishakha", "Jyeshtha", "Ashadha", "Shravana", "Bhadrapada", "Ashwayuja", "Kartika", "Margashira", "Pushya", "Magha", "Phalguna"],
      te: ["చైత్రం", "వైశాఖం", "జ్యేష్ఠం", "ఆషాఢం", "శ్రావణం", "భాద్రపదం", "ఆశ్వయుజం", "కార్తీకం", "మార్గశిరం", "పుష్యం", "మాఘం", "ఫాల్గుణం"],
      hi: ["चैत्र", "वैशाख", "ज्येष्ठ", "आषाढ़", "श्रावण", "भाद्रपद", "आश्विन", "कार्तिक", "मार्गशीर्ष", "पौष", "माघ", "फाल्गुन"],
      mr: ["चैत्र", "वैशाख", "ज्येष्ठ", "आषाढ", "श्रावण", "भाद्रपद", "आश्विन", "कार्तिक", "मार्गशीर्ष", "पौष", "माघ", "फाल्गुन"],
    },
    YOGA_EN: ["Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana", "Atiganda", "Sukarma", "Dhriti", "Shoola", "Ganda", "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra", "Siddhi", "Vyatipata", "Variyan", "Parigha", "Shiva", "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma", "Indra", "Vaidhriti"],
    KARANA_EN: ["Kimstughna", "Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Vishti", "Shakuni", "Chatushpada", "Naga"],
    SAMVATSARA_EN: ["Prabhava", "Vibhava", "Shukla", "Pramoda", "Prajapati", "Angirasa", "Shrimukha", "Bhava", "Yuva", "Dhatu", "Ishvara", "Bahudhanya", "Pramathi", "Vikrama", "Vrisha", "Chitrabhanu", "Svabhanu", "Tarana", "Parthiva", "Vyaya", "Sarvajit", "Sarvadhari", "Virodhi", "Vikriti", "Khara", "Nandana", "Vijaya", "Jaya", "Manmatha", "Durmukhi", "Hevilambi", "Vilambi", "Vikari", "Sharvari", "Plava", "Shubhakrit", "Shobhakrit", "Krodhi", "Vishvavasu", "Parabhava", "Plavanga", "Kilaka", "Saumya", "Sadharana", "Virodhikrit", "Paridhavi", "Pramadi", "Ananda", "Rakshasa", "Nala", "Pingala", "Kalayukti", "Siddharthi", "Raudri", "Durmati", "Dundubhi", "Rudhirodgari", "Raktakshi", "Krodhana", "Akshaya"],
    ADHIKA: { en: "Adhika", te: "అధిక", hi: "अधिक", mr: "अधिक" },
    TARA_EN: ["Janma", "Sampat", "Vipat", "Kshema", "Pratyak", "Sadhana", "Naidhana", "Mitra", "Parama Mitra"],
    LAGNA_TYPE_EN: ["Chara (movable)", "Sthira (fixed)", "Dvisvabhava (dual)"],
  };
  L.NAKSHATRA.mr = L.NAKSHATRA.hi.map((n) => n.replace(/ढ़/g, "ढ"));
  const nm = (table, i, lang) => (table[lang] || table.en)[i];

  function nakIndexFromName(s) {
    if (!s) return null;
    const key = String(s).trim().toLowerCase().replace(/-/g, " ").replace(/\s+/g, " ");
    const aliases = { aswini: 0, ashvini: 0, bharni: 1, kritika: 2, karthika: 2, krithika: 2, mrigasira: 4, mrigashirsha: 4, mrugasira: 4, arudra: 5, aardra: 5, pushyami: 7, pushya: 7, aslesha: 8, ashlesha: 8, makha: 9, magam: 9, pubba: 10, "purva phalguni": 10, "poorva phalguni": 10, uttara: 11, uttaram: 11, "uttara phalguni": 11, chitta: 13, chithra: 13, swathi: 14, swati: 14, visakha: 15, anuradha: 16, anusham: 16, jyeshta: 17, jyestha: 17, mula: 18, moolam: 18, purvashadha: 19, poorvashada: 19, "purva ashadha": 19, uttarashadha: 20, uttarashada: 20, sravana: 21, shravanam: 21, dhanishtha: 22, shatabhisham: 23, satabhisha: 23, purvabhadra: 24, "purva bhadra": 24, uttarabhadra: 25, "uttara bhadra": 25, revathi: 26 };
    if (key in aliases) return aliases[key];
    for (const lang of Object.keys(L.NAKSHATRA)) {
      const i = L.NAKSHATRA[lang].findIndex((n) => n.toLowerCase() === key || n.toLowerCase().replace(/ /g, "") === key.replace(/ /g, ""));
      if (i >= 0) return i;
    }
    return null;
  }
  function rashiIndexFromName(s) {
    if (!s) return null;
    const key = String(s).trim().toLowerCase();
    const western = ["aries", "taurus", "gemini", "cancer", "leo", "virgo", "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"];
    const aliases = { vrushabha: 1, vrishabham: 1, mithunam: 2, karkataka: 3, karkatakam: 3, kark: 3, simham: 4, singh: 4, kanni: 5, thula: 6, tulam: 6, vrischikam: 7, vrishchika: 7, dhanus: 8, dhanussu: 8, dhanur: 8, makaram: 9, kumbham: 10, meenam: 11, mesham: 0 };
    if (western.includes(key)) return western.indexOf(key);
    if (key in aliases) return aliases[key];
    for (const lang of Object.keys(L.RASHI)) {
      const i = L.RASHI[lang].findIndex((n) => n.toLowerCase() === key);
      if (i >= 0) return i;
    }
    return null;
  }

  // ------------------------------------------------------------------ time zones
  const fmtCache = {};
  function tzParts(ms, tz) {
    if (tz === "Asia/Kolkata") {
      const d = new Date(ms + 330 * 60000);
      return { y: d.getUTCFullYear(), m: d.getUTCMonth() + 1, d: d.getUTCDate(), H: d.getUTCHours(), M: d.getUTCMinutes(), S: d.getUTCSeconds() };
    }
    const f = fmtCache[tz] || (fmtCache[tz] = new Intl.DateTimeFormat("en-US", { timeZone: tz, hourCycle: "h23", year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", second: "2-digit" }));
    const p = {};
    for (const x of f.formatToParts(new Date(ms))) p[x.type] = x.value;
    return { y: +p.year, m: +p.month, d: +p.day, H: +p.hour % 24, M: +p.minute, S: +p.second };
  }
  function tzOffsetMin(ms, tz) {
    if (tz === "Asia/Kolkata") return 330;
    const p = tzParts(ms, tz);
    return Math.round((Date.UTC(p.y, p.m - 1, p.d, p.H, p.M, p.S) - ms) / 60000);
  }
  function localToMs(y, m, d, H, M, tz) {
    const guess = Date.UTC(y, m - 1, d, H, M);
    let off = tzOffsetMin(guess, tz);
    off = tzOffsetMin(guess - off * 60000, tz);
    return guess - off * 60000;
  }
  const localToUt = (y, m, d, H, M, tz) => msToUt(localToMs(y, m, d, H, M, tz));
  const pad = (n) => String(n).padStart(2, "0");
  function utParts(ut, tz) { return tzParts(Math.floor(utToMs(ut) / 1000) * 1000, tz); }
  function fmt(ut, tz) { const p = utParts(ut, tz); return `${p.y}-${pad(p.m)}-${pad(p.d)} ${pad(p.H)}:${pad(p.M)}`; }
  function hm(ut, tz) { const p = utParts(ut, tz); return `${pad(p.H)}:${pad(p.M)}`; }
  function hm12(ut, tz) { const p = utParts(ut, tz); const h = p.H % 12 || 12; return `${pad(h)}:${pad(p.M)} ${p.H < 12 ? "AM" : "PM"}`; }
  function civilDate(ut, tz) { const p = utParts(ut, tz); return `${p.y}-${pad(p.m)}-${pad(p.d)}`; }
  function parseISODate(s) { const [y, m, d] = s.split("-").map(Number); return { y, m, d }; }
  function addDays(s, n) { const { y, m, d } = parseISODate(s); const x = new Date(Date.UTC(y, m - 1, d + n)); return `${x.getUTCFullYear()}-${pad(x.getUTCMonth() + 1)}-${pad(x.getUTCDate())}`; }
  function daysBetween(a, b) { const p = parseISODate(a), q = parseISODate(b); return Math.round((Date.UTC(q.y, q.m - 1, q.d) - Date.UTC(p.y, p.m - 1, p.d)) / 86400000); }
  function weekdayOf(s) { const { y, m, d } = parseISODate(s); return new Date(Date.UTC(y, m - 1, d)).getUTCDay(); }
  function todayIn(tz) { return civilDate(msToUt(Date.now()), tz || "Asia/Kolkata"); }

  // ------------------------------------------------------------------ ephemeris
  const LAHIRI_J2000 = 23.857092;
  function meanAyanamsa(ut) { const t = ut / 36525; return LAHIRI_J2000 + (5028.796195 * t + 1.1054348 * t * t + 0.00007964 * t ** 3) / 3600; }
  const tiltCache = new Map();
  function tilt(ut) { const k = r5(ut); let v = tiltCache.get(k); if (!v) { v = A.e_tilt(T(k)); tiltCache.set(k, v); } return v; }
  const trueAyanamsa = (ut) => meanAyanamsa(ut) + tilt(ut).dpsi / 3600;
  function meanNode(ut) { const t = ut / 36525; return norm(125.0445479 - 1934.1362891 * t + 0.0020754 * t * t + t ** 3 / 467441.0); }
  const BODY = { Sun: "Sun", Moon: "Moon", Mars: "Mars", Mercury: "Mercury", Jupiter: "Jupiter", Venus: "Venus", Saturn: "Saturn" };
  const posCache = new Map();
  function sid(body, ut0) {
    const ut = r5(ut0); const k = body + ut; let v = posCache.get(k);
    if (v !== undefined) return v;
    let trop;
    if (body === "Rahu") trop = meanNode(ut) + tilt(ut).dpsi / 3600;
    else if (body === "Ketu") trop = meanNode(ut) + tilt(ut).dpsi / 3600 + 180;
    else if (body === "Sun") trop = A.SunPosition(T(ut)).elon;
    else if (body === "Moon") trop = A.EclipticGeoMoon(T(ut)).lon;
    else trop = A.Ecliptic(A.GeoVector(BODY[body], T(ut), true)).elon;
    v = norm(trop - trueAyanamsa(ut));
    if (posCache.size > 400000) posCache.clear();
    posCache.set(k, v);
    return v;
  }
  const sun = (ut) => sid("Sun", ut);
  const moon = (ut) => sid("Moon", ut);
  const PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"];
  function allPlanets(ut) { const o = {}; for (const p of PLANETS) o[p] = sid(p, ut); return o; }
  function isRetro(body, ut) { const a = sid(body, ut - 0.5), b = sid(body, ut + 0.5); return ((b - a + 540) % 360) - 180 < 0; }
  function angSep(a, b) { const d = Math.abs(norm(a) - norm(b)) % 360; return Math.min(d, 360 - d); }
  function ascendant(ut, lat, lon) {
    const gast = A.SiderealTime(T(ut));
    const ramc = (norm(gast * 15 + lon) * Math.PI) / 180;
    const eps = (tilt(ut).tobl * Math.PI) / 180, phi = (lat * Math.PI) / 180;
    const asc = (Math.atan2(Math.cos(ramc), -(Math.sin(ramc) * Math.cos(eps) + Math.tan(phi) * Math.sin(eps))) * 180) / Math.PI;
    return norm(asc - trueAyanamsa(ut));
  }
  const riseCache = new Map();
  function riseSet(kind, ut, lat, lon) {
    const k = kind + r5(ut) + "," + lat + "," + lon; if (riseCache.has(k)) return riseCache.get(k);
    const r = A.SearchRiseSet("Sun", new A.Observer(lat, lon, 0), kind === "rise" ? +1 : -1, T(r5(ut)), 2);
    const v = r ? r.ut : null; riseCache.set(k, v); return v;
  }
  function previousNewMoon(ut) {
    let last = A.SearchMoonPhase(0, T(ut - 31), 31).ut;
    for (;;) { const n = A.SearchMoonPhase(0, T(last + 1), 31); if (!n || n.ut > ut) return last; last = n.ut; }
  }
  const nextNewMoon = (ut) => A.SearchMoonPhase(0, T(ut), 32).ut;
  const eclCache = new Map();
  function eclipsesBetween(ut0, ut1, lat, lon) {
    const k = [ut0, ut1, lat, lon].join(","); if (eclCache.has(k)) return eclCache.get(k);
    const obs = new A.Observer(lat, lon, 0); const out = [];
    let e = A.SearchLunarEclipse(T(ut0));
    while (e.peak.ut <= ut1) {
      if (e.kind !== "penumbral") {
        const half = e.sd_partial / 1440;
        for (let i = 0; i < 9; i++) {
          const tt = e.peak.AddDays(-half + (i * half) / 4);
          const eq = A.Equator("Moon", tt, obs, true, true);
          if (A.Horizon(tt, obs, eq.ra, eq.dec, "normal").altitude > 0) { out.push(["lunar", e.peak.ut]); break; }
        }
      }
      e = A.NextLunarEclipse(e.peak);
    }
    let s = A.SearchLocalSolarEclipse(T(ut0), obs);
    while (s.peak.time.ut <= ut1) {
      if (Math.max(s.partial_begin.altitude, s.peak.altitude, s.partial_end.altitude) > 0) out.push(["solar", s.peak.time.ut]);
      s = A.NextLocalSolarEclipse(s.peak.time, obs);
    }
    out.sort((a, b) => a[1] - b[1]); eclCache.set(k, out); return out;
  }

  // ------------------------------------------------------------------ panchang
  const elong = (ut) => norm(moon(ut) - sun(ut));
  const yogaAngle = (ut) => norm(moon(ut) + sun(ut));
  const ELEMENTS = { tithi: [elong, 12, 12.19], nakshatra: [moon, NAK, 13.18], yoga: [yogaAngle, NAK, 14.17], karana: [elong, 6, 12.19], moon_rashi: [moon, 30, 13.18] };
  function crossing(fn, ut0, target, rate) {
    let ut = ut0;
    for (let i = 0; i < 40; i++) {
      let diff = (((target - fn(ut)) % 360) + 360) % 360;
      if (diff > 300) diff -= 360;
      if (Math.abs(diff) < 2e-5) return ut;
      const h = 0.02; const lr = ((((fn(ut + h) - fn(ut)) % 360) + 360) % 360) / h || rate;
      ut += diff / lr;
    }
    return ut;
  }
  function elementSpans(kind, a, b) {
    const [fn, size, rate] = ELEMENTS[kind]; const spans = [];
    const ang = fn(a); let idx = Math.floor(ang / size);
    const back = (ang - idx * size) / rate;
    let start = crossing(fn, a - back - 0.08, norm(idx * size), rate);
    if (start > a) start = crossing(fn, a - back - 0.6, norm(idx * size), rate);
    const n = Math.round(360 / size); let cur = start;
    for (;;) {
      const nxt = (idx + 1) % n; const end = crossing(fn, cur + 0.01, norm(nxt * size), rate);
      spans.push({ index: idx, start: cur, end });
      if (end >= b) break; idx = nxt; cur = end;
    }
    return spans;
  }
  const karanaName = (h) => (h === 0 ? 0 : h <= 56 ? 1 + ((h - 1) % 7) : { 57: 8, 58: 9, 59: 10 }[h]);
  const masaCache = new Map();
  function lunarMonth(ut) {
    const nm0 = previousNewMoon(ut); const k = Math.round(nm0 * 1e4) / 1e4;
    if (!masaCache.has(k)) {
      const nm1 = nextNewMoon(k + 1); const s0 = Math.floor(sun(k) / 30), s1 = Math.floor(sun(nm1) / 30);
      masaCache.set(k, { masa: (s0 + 1) % 12, adhika: s0 === s1 });
    }
    return masaCache.get(k);
  }
  function samvatsaraIndex(dateStr, masa, adhika) {
    const { y, m } = parseISODate(dateStr); let shaka = y - 78;
    if (m <= 4 && (masa >= 9 || (masa === 0 && adhika))) shaka -= 1;
    return (((shaka + 11) % 60) + 60) % 60;
  }
  const RAHU_PART = [8, 2, 7, 5, 6, 4, 3], YAMA_PART = [5, 4, 3, 2, 1, 7, 6], GULIKA_PART = [7, 6, 5, 4, 3, 2, 1];
  const DUR_DAY = [[14], [9, 12], [4], [8], [6, 12], [4, 9], [1, 2]], DUR_NIGHT = [[], [], [7], [], [], [], []];
  const VARJYAM = [50, 24, 30, 40, 14, 11, 30, 20, 32, 30, 20, 18, 22, 20, 14, 14, 10, 14, 20, 24, 20, 10, 10, 18, 16, 24, 30];
  const AMRITA = [42, 48, 54, 52, 38, 35, 54, 44, 56, 54, 44, 42, 45, 44, 38, 38, 34, 38, 44, 48, 44, 34, 34, 42, 40, 48, 54];
  const part = (sr, ss, n, k) => { const st = (ss - sr) / n; return [sr + (k - 1) * st, sr + k * st]; };
  function lagnaSpans(a, b, lat, lon) {
    const step = 4 / 1440; const spans = []; let cur = Math.floor(ascendant(a, lat, lon) / 30), start = a, t = a;
    while (t < b) {
      const t2 = Math.min(t + step, b); const s2 = Math.floor(ascendant(t2, lat, lon) / 30);
      if (s2 !== cur) {
        let lo = t, hi = t2;
        for (let i = 0; i < 20; i++) { const mid = (lo + hi) / 2; if (Math.floor(ascendant(mid, lat, lon) / 30) === cur) lo = mid; else hi = mid; }
        spans.push({ index: cur, start, end: hi }); cur = s2; start = hi;
      }
      t = t2;
    }
    spans.push({ index: cur, start, end: b });
    return spans;
  }
  function moudhyam(ut) {
    const s = sun(ut);
    const guru = angSep(sid("Jupiter", ut), s) < 11;
    const shukra = angSep(sid("Venus", ut), s) < (isRetro("Venus", ut) ? 8 : 10);
    return [guru, shukra];
  }
  const spanAt = (spans, t) => { for (const s of spans) if (s.start <= t && t < s.end) return s.index; return t >= spans[spans.length - 1].start ? spans[spans.length - 1].index : spans[0].index; };
  const dayCache = new Map();
  function dayPanchang(dateStr, place) {
    const key = dateStr + "|" + place.lat + "|" + place.lon + "|" + place.tz;
    if (dayCache.has(key)) return dayCache.get(key);
    const { y, m, d } = parseISODate(dateStr);
    const ut0 = localToUt(y, m, d, 0, 0, place.tz);
    const sr = riseSet("rise", ut0, place.lat, place.lon);
    const ss = riseSet("set", sr, place.lat, place.lon);
    const nsr = riseSet("rise", ss, place.lat, place.lon);
    const tithis = elementSpans("tithi", sr, nsr), naks = elementSpans("nakshatra", sr, nsr), yogas = elementSpans("yoga", sr, nsr);
    const karanas = elementSpans("karana", sr, nsr).map((h) => ({ index: karanaName(h.index), start: h.start, end: h.end }));
    const mr = elementSpans("moon_rashi", sr, nsr), lagnas = lagnaSpans(sr, nsr, place.lat, place.lon);
    const { masa, adhika } = lunarMonth(sr);
    const vara = weekdayOf(dateStr);
    const varj = [], amr = [];
    for (const sp of elementSpans("nakshatra", sr - 1.1, nsr + 0.1)) {
      const dur = sp.end - sp.start;
      for (const [tab, out] of [[VARJYAM, varj], [AMRITA, amr]]) {
        const vs = sp.start + (dur * tab[sp.index]) / 60, ve = vs + (dur * 4) / 60;
        if (vs < nsr && ve > sr) out.push([vs, ve]);
      }
    }
    const [gm, sm] = moudhyam(sr);
    const p = {
      date: dateStr, place, sunrise: sr, sunset: ss, next_sunrise: nsr, vara, tithis, nakshatras: naks, yogas, karanas, lagnas,
      masa, adhika, samvatsara: samvatsaraIndex(dateStr, masa, adhika), sun_rashi: Math.floor(sun(sr) / 30), moon_rashis: mr,
      rahu: part(sr, ss, 8, RAHU_PART[vara]), yamaganda: part(sr, ss, 8, YAMA_PART[vara]), gulika: part(sr, ss, 8, GULIKA_PART[vara]),
      durmuhurtas: DUR_DAY[vara].map((k) => part(sr, ss, 15, k)).concat(DUR_NIGHT[vara].map((k) => part(ss, nsr, 15, k))),
      varjyams: varj, amritas: amr, abhijit: part(sr, ss, 15, 8), guru_moudhyam: gm, shukra_moudhyam: sm,
    };
    p.at = (spans, t) => spanAt(spans, t);
    dayCache.set(key, p);
    return p;
  }
  function tithiLabel(i, lang) {
    const paksha = i < 15 ? 0 : 1; let n = i < 15 ? i : i - 15; if (i === 29) n = 15;
    return `${nm(L.PAKSHA, paksha, lang)} ${nm(L.TITHI, n, lang)}`;
  }
  function panchangDict(p, lang = "en") {
    const tz = p.place.tz;
    const spans = (lst, lab) => lst.map((s) => ({ name: lab(s.index), index: s.index, from: fmt(s.start, tz), to: fmt(s.end, tz) }));
    let masa = nm(L.MASA, p.masa, lang); if (p.adhika) masa = `${L.ADHIKA[lang] || "Adhika"} ${masa}`;
    return {
      date: p.date, place: { name: p.place.name, lat: p.place.lat, lon: p.place.lon, tz },
      samvatsara: L.SAMVATSARA_EN[p.samvatsara], masa, masa_index: p.masa, adhika_masa: p.adhika, vara: nm(L.VARA, p.vara, lang),
      sunrise: hm(p.sunrise, tz), sunset: hm(p.sunset, tz),
      tithi: spans(p.tithis, (i) => tithiLabel(i, lang)), nakshatra: spans(p.nakshatras, (i) => nm(L.NAKSHATRA, i, lang)),
      yoga: spans(p.yogas, (i) => L.YOGA_EN[i]), karana: spans(p.karanas, (i) => L.KARANA_EN[i]),
      moon_rashi: spans(p.moon_rashis, (i) => nm(L.RASHI, i, lang)), sun_rashi: nm(L.RASHI, p.sun_rashi, lang),
      lagna: spans(p.lagnas, (i) => nm(L.RASHI, i, lang)),
      rahu_kalam: p.rahu.map((x) => hm(x, tz)), yamagandam: p.yamaganda.map((x) => hm(x, tz)), gulika_kalam: p.gulika.map((x) => hm(x, tz)),
      durmuhurtham: p.durmuhurtas.map(([a, b]) => [fmt(a, tz), fmt(b, tz)]), varjyam: p.varjyams.map(([a, b]) => [fmt(a, tz), fmt(b, tz)]),
      amrita_kalam: p.amritas.map(([a, b]) => [fmt(a, tz), fmt(b, tz)]), abhijit: p.abhijit.map((x) => hm(x, tz)),
      guru_moudhyam: p.guru_moudhyam, shukra_moudhyam: p.shukra_moudhyam,
    };
  }
  function janmaFromBirth(dob, tob, place) {
    const { y, m, d } = parseISODate(dob);
    if (tob) {
      const [H, M] = tob.split(":").map(Number); const mo = moon(localToUt(y, m, d, H, M, place.tz));
      return { nakshatra: Math.floor(mo / NAK), pada: Math.floor((mo % NAK) / (NAK / 4)) + 1, rashi: Math.floor(mo / 30), certain: true, note: "" };
    }
    const a = moon(localToUt(y, m, d, 0, 0, place.tz)), b = moon(localToUt(y, m, d, 23, 59, place.tz)), mo = moon(localToUt(y, m, d, 12, 0, place.tz));
    const sameN = Math.floor(a / NAK) === Math.floor(b / NAK), sameR = Math.floor(a / 30) === Math.floor(b / 30);
    return { nakshatra: Math.floor(mo / NAK), pada: Math.floor((mo % NAK) / (NAK / 4)) + 1, rashi: Math.floor(mo / 30), certain: sameN && sameR,
      note: sameN ? "" : "Birth star changed during the day of birth; birth time or known nakshatra needed." };
  }

  // ------------------------------------------------------------------ rule book (events.py)
  const NI = {}; L.NAKSHATRA.en.forEach((n, i) => (NI[n.toLowerCase()] = i));
  const N = (...names) => new Set(names.map((n) => { const i = NI[n.toLowerCase()]; if (i === undefined) throw new Error("bad nak " + n); return i; }));
  const S = (...xs) => new Set(xs);
  const U = (...sets) => new Set(sets.flatMap((s) => [...s]));
  const [SUN, MON, TUE, WED, THU, FRI, SAT] = [0, 1, 2, 3, 4, 5, 6];
  const [CHAITRA, VAISHAKHA, JYESHTHA, ASHADHA, SHRAVANA, BHADRAPADA, ASHWAYUJA, KARTIKA, MARGASHIRA, PUSHYA, MAGHA, PHALGUNA] = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11];
  const DHRUVA = N("Rohini", "Uttara Phalguni", "Uttara Ashadha", "Uttara Bhadrapada");
  const MRIDU = N("Mrigashira", "Chitra", "Anuradha", "Revati");
  const KSHIPRA = N("Ashwini", "Pushya", "Hasta");
  const CHARA_NAK = N("Punarvasu", "Swati", "Shravana", "Dhanishta", "Shatabhisha");
  const BAD_YOGAS = S(0, 5, 8, 9, 12, 14, 16, 18, 26), WORST_YOGAS = S(16, 26);
  const SARVARTHA = {
    0: N("Ashwini", "Pushya", "Hasta", "Uttara Phalguni", "Uttara Ashadha", "Uttara Bhadrapada", "Moola"),
    1: N("Rohini", "Mrigashira", "Pushya", "Anuradha", "Shravana"), 2: N("Ashwini", "Krittika", "Ashlesha", "Uttara Bhadrapada"),
    3: N("Rohini", "Anuradha", "Hasta", "Krittika", "Mrigashira"), 4: N("Ashwini", "Punarvasu", "Pushya", "Anuradha", "Revati"),
    5: N("Ashwini", "Punarvasu", "Anuradha", "Shravana", "Revati"), 6: N("Rohini", "Swati", "Shravana"),
  };
  const SWAYAM = { [`${CHAITRA},0,1`]: "Ugadi / Gudi Padwa", [`${VAISHAKHA},0,3`]: "Akshaya Tritiya", [`${ASHWAYUJA},0,10`]: "Vijayadashami", [`${KARTIKA},0,1`]: "Bali Pratipada", [`${MAGHA},0,5`]: "Vasant Panchami" };
  const ALLR = (ms) => ({ telugu: new Set(ms), marathi: new Set(ms), north: new Set(ms) });
  const person = (role, label, required = true) => [
    { key: `${role}.name`, label: `${label} - full name`, required },
    { key: `${role}.dob`, label: `${label} - date of birth`, required },
    { key: `${role}.tob`, label: `${label} - time of birth`, required: false, hint: "If not known, ask for janma nakshatra / rashi instead" },
    { key: `${role}.birthplace`, label: `${label} - place of birth`, required },
  ];
  const COMMON = [
    { key: "window", label: "Preferred date range (from - to)", required: true, hint: "Ideally 1-6 months" },
    { key: "venue_city", label: "City / place where the event will happen", required: true },
    { key: "time_pref", label: "Preferred time of day (morning / afternoon / evening / night / any)", required: false },
    { key: "avoid_dates", label: "Dates that are NOT possible for the family", required: false },
  ];
  const DEF = {
    best_nakshatras: new Set(), varas: S(MON, WED, THU, FRI), ok_varas: new Set(),
    tithi_good_s: S(2, 3, 5, 7, 10, 11, 13), tithi_ok_s: S(1, 6, 12, 15), tithi_good_k: S(1, 2, 3, 5), tithi_ok_k: S(6, 7, 10, 11, 12, 13),
    period: "day", lagna_pref: "any", lagna_strict: false, moudhyam: false, no_adhika: true, months: null, ok_months: null,
    avoid_dhanurmasa: false, avoid_chaturmasa: null, avoid_pitru_paksha: true, avoid_bad_yoga: true, avoid_vishti: true,
    personal_roles: ["kartha"], swayam_siddha_override: false, min_minutes: 24, requirements: [], notes: [],
  };
  const EVENTS = {};
  const add = (e) => (EVENTS[e.code] = Object.assign({}, DEF, e));
  const VIVAHA_NAK = N("Rohini", "Mrigashira", "Magha", "Uttara Phalguni", "Hasta", "Swati", "Anuradha", "Moola", "Uttara Ashadha", "Uttara Bhadrapada", "Revati");
  add({ code: "vivaha", name: "Vivaha (Marriage)", aliases: ["marriage", "wedding", "pelli", "shaadi", "lagna", "vivah", "kalyanam", "lagnam"],
    nakshatras: VIVAHA_NAK, best_nakshatras: N("Rohini", "Uttara Phalguni", "Uttara Ashadha", "Uttara Bhadrapada", "Revati", "Mrigashira", "Hasta"),
    ok_varas: S(SUN), tithi_ok_s: S(1, 12, 15), tithi_ok_k: S(7, 10), period: "any", lagna_strict: true, moudhyam: true,
    months: { telugu: S(CHAITRA, VAISHAKHA, JYESHTHA, SHRAVANA, KARTIKA, MARGASHIRA, MAGHA, PHALGUNA), marathi: S(KARTIKA, MARGASHIRA, PUSHYA, MAGHA, PHALGUNA, CHAITRA, VAISHAKHA, JYESHTHA), north: S(KARTIKA, MARGASHIRA, MAGHA, PHALGUNA, VAISHAKHA, JYESHTHA, ASHADHA) },
    avoid_dhanurmasa: true, avoid_chaturmasa: { marathi: true, north: true, telugu: false }, personal_roles: ["bride", "groom"], min_minutes: 30,
    requirements: [...person("bride", "Bride"), ...person("groom", "Groom"), ...COMMON, { key: "first_child", label: "Is either of them the eldest child? (Jyeshtha masa check)", required: false }],
    notes: ["Guru bala for the bride and Surya bala for the groom are scored, not enforced; pandit may prescribe shanti where weak.", "Telugu custom avoids Jyeshtha masa when the bride or groom is the eldest child."] });
  add({ code: "nischitartham", name: "Nischitartham / Sagai (Engagement)", aliases: ["engagement", "sagai", "nischitartham", "roka", "ring ceremony", "sakharpuda", "tilak"],
    nakshatras: U(VIVAHA_NAK, N("Pushya", "Shravana", "Dhanishta", "Chitra", "Punarvasu")), ok_varas: S(SUN), lagna_pref: "sthira_dvi", moudhyam: true,
    avoid_chaturmasa: { north: true }, personal_roles: ["bride", "groom"], requirements: [...person("bride", "Bride"), ...person("groom", "Groom"), ...COMMON] });
  add({ code: "griha_pravesh", name: "Griha Pravesh (House warming)", aliases: ["griha pravesh", "gruhapravesam", "housewarming", "house warming", "new house", "grihapravesh", "vastu shanti", "graha pravesam"],
    nakshatras: U(DHRUVA, MRIDU, N("Dhanishta", "Shatabhisha", "Pushya", "Shravana")), best_nakshatras: U(DHRUVA, MRIDU), ok_varas: S(SAT),
    tithi_ok_s: S(12, 15), tithi_good_k: S(2, 3, 5), tithi_ok_k: S(7, 10, 11), lagna_pref: "sthira", moudhyam: true,
    months: { telugu: S(VAISHAKHA, JYESHTHA, SHRAVANA, KARTIKA, MARGASHIRA, MAGHA, PHALGUNA), marathi: S(VAISHAKHA, JYESHTHA, KARTIKA, MARGASHIRA, MAGHA, PHALGUNA), north: S(VAISHAKHA, JYESHTHA, KARTIKA, MARGASHIRA, MAGHA, PHALGUNA) },
    ok_months: { telugu: S(SHRAVANA, KARTIKA, MARGASHIRA), marathi: S(KARTIKA, MARGASHIRA), north: S(KARTIKA, MARGASHIRA) },
    avoid_dhanurmasa: true, avoid_chaturmasa: { marathi: true, north: true },
    requirements: [...person("kartha", "Head of the family (owner)"), ...COMMON, { key: "house_facing", label: "Main door facing direction (optional)", required: false }],
    notes: ["Sthira lagna is preferred so the family stays settled in the home."] });
  add({ code: "bhoomi_puja", name: "Bhoomi Puja / Shankusthapana (Foundation)", aliases: ["bhoomi puja", "bhumi pujan", "shankusthapana", "foundation", "construction start", "bhoomi pooja", "slab", "groundbreaking"],
    nakshatras: N("Rohini", "Mrigashira", "Pushya", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Anuradha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Uttara Bhadrapada", "Revati"),
    best_nakshatras: U(DHRUVA, MRIDU), ok_varas: S(SAT), lagna_pref: "sthira", moudhyam: true, months: ALLR([VAISHAKHA, SHRAVANA, KARTIKA, MARGASHIRA, MAGHA, PHALGUNA]),
    requirements: [...person("kartha", "Owner of the land"), ...COMMON, { key: "plot_facing", label: "Plot facing direction (optional)", required: false }] });
  add({ code: "property_purchase", name: "Property / Land Purchase or Registration", aliases: ["property", "land purchase", "registration", "flat purchase", "plot", "house purchase", "registry", "agreement"],
    nakshatras: N("Rohini", "Mrigashira", "Punarvasu", "Pushya", "Magha", "Uttara Phalguni", "Hasta", "Vishakha", "Anuradha", "Moola", "Uttara Ashadha", "Shravana", "Uttara Bhadrapada", "Revati"),
    best_nakshatras: U(DHRUVA, N("Mrigashira", "Pushya", "Revati")), ok_varas: S(SUN, SAT), lagna_pref: "sthira", swayam_siddha_override: true, no_adhika: false,
    requirements: [...person("kartha", "Buyer"), ...COMMON] });
  add({ code: "vehicle_purchase", name: "Vahana (Vehicle purchase / delivery)", aliases: ["vehicle", "car", "bike", "vahana", "vahan", "two wheeler", "scooter", "car delivery"],
    nakshatras: N("Ashwini", "Mrigashira", "Punarvasu", "Pushya", "Hasta", "Chitra", "Swati", "Anuradha", "Shravana", "Dhanishta", "Shatabhisha", "Revati", "Rohini", "Uttara Phalguni", "Uttara Ashadha", "Uttara Bhadrapada"),
    best_nakshatras: U(KSHIPRA, CHARA_NAK, N("Revati")), ok_varas: S(SUN), lagna_pref: "chara", swayam_siddha_override: true, no_adhika: false,
    requirements: [...person("kartha", "Owner / buyer"), ...COMMON] });
  add({ code: "vyapara", name: "Vyapara Arambha (Business / shop / office opening)", aliases: ["business", "shop opening", "office opening", "new business", "startup launch", "dukan", "udghatan", "inauguration", "company launch", "showroom", "factory"],
    nakshatras: N("Ashwini", "Rohini", "Mrigashira", "Pushya", "Uttara Phalguni", "Hasta", "Chitra", "Anuradha", "Uttara Ashadha", "Shravana", "Dhanishta", "Uttara Bhadrapada", "Revati"),
    best_nakshatras: U(KSHIPRA, DHRUVA, N("Revati")), ok_varas: S(SUN), lagna_pref: "sthira", swayam_siddha_override: true,
    requirements: [...person("kartha", "Owner / main partner"), ...COMMON, { key: "business_type", label: "Type of business (optional)", required: false }] });
  add({ code: "job_joining", name: "Joining a new job / starting a new role", aliases: ["job", "joining", "new job", "naukri", "office joining", "new role"],
    nakshatras: N("Ashwini", "Rohini", "Mrigashira", "Punarvasu", "Pushya", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Anuradha", "Uttara Ashadha", "Shravana", "Dhanishta", "Uttara Bhadrapada", "Revati"),
    varas: S(SUN, MON, WED, THU, FRI), lagna_pref: "sthira_dvi", no_adhika: false, avoid_pitru_paksha: false, requirements: [...person("kartha", "Person joining"), ...COMMON] });
  add({ code: "jewellery_purchase", name: "Gold / Jewellery purchase", aliases: ["gold", "jewellery", "jewelry", "silver", "ornaments", "sona", "bangaram"],
    nakshatras: N("Ashwini", "Rohini", "Punarvasu", "Pushya", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Anuradha", "Shravana", "Dhanishta", "Uttara Ashadha", "Uttara Bhadrapada", "Revati"),
    best_nakshatras: N("Pushya", "Rohini", "Revati", "Ashwini"), varas: S(SUN, MON, WED, THU, FRI), lagna_pref: "sthira", swayam_siddha_override: true, no_adhika: false,
    requirements: [...person("kartha", "Buyer", false), ...COMMON] });
  add({ code: "yatra", name: "Yatra (Travel / pilgrimage start)", aliases: ["travel", "journey", "trip", "pilgrimage", "yatra", "teerth", "relocation", "moving abroad"],
    nakshatras: N("Ashwini", "Mrigashira", "Punarvasu", "Pushya", "Hasta", "Anuradha", "Shravana", "Dhanishta", "Revati"), varas: S(0, 1, 2, 3, 4, 5, 6),
    lagna_pref: "chara", no_adhika: false, avoid_pitru_paksha: false,
    requirements: [...person("kartha", "Main traveller"), ...COMMON, { key: "direction", label: "Direction of travel from home (north/south/east/west)", required: true }],
    notes: ["Disha-shoola (weekday vs direction) is enforced."] });
  const CHILD = [...person("child", "Child"), ...person("father", "Father", false)];
  const CHILD_NAK16 = N("Ashwini", "Rohini", "Mrigashira", "Punarvasu", "Pushya", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Anuradha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Uttara Bhadrapada", "Revati");
  add({ code: "namakarana", name: "Namakarana (Naming ceremony)", aliases: ["naming", "naming ceremony", "namakaran", "barasala", "naamkaran", "baarse", "cradle"],
    nakshatras: CHILD_NAK16, ok_varas: S(SUN), lagna_pref: "sthira_dvi", no_adhika: false, avoid_pitru_paksha: false, personal_roles: ["child"],
    requirements: [...CHILD, ...COMMON, { key: "child.gender", label: "Child's gender", required: true }], notes: ["Traditionally on the 11th, 12th or 16th day after birth, or any good day later."] });
  add({ code: "annaprashana", name: "Annaprashana (First rice feeding)", aliases: ["annaprashana", "annaprasana", "first rice", "first food", "mukhe bhaat", "annaprasan"],
    nakshatras: CHILD_NAK16, period: "morning", lagna_pref: "sthira_dvi", personal_roles: ["child"],
    requirements: [...CHILD, ...COMMON, { key: "child.gender", label: "Child's gender", required: true }], notes: ["Boys in even months (6th, 8th), girls in odd months (5th, 7th) of age - engine checks this."] });
  add({ code: "chudakarana", name: "Chudakarana / Mundan (First haircut)", aliases: ["mundan", "chudakarana", "first haircut", "tonsure", "puttu ventrukalu", "javal", "choula"],
    nakshatras: N("Ashwini", "Mrigashira", "Punarvasu", "Pushya", "Hasta", "Chitra", "Swati", "Jyeshtha", "Shravana", "Dhanishta", "Shatabhisha", "Revati"),
    period: "morning", personal_roles: ["child"], avoid_chaturmasa: { north: true }, requirements: [...CHILD, ...COMMON, { key: "child.gender", label: "Child's gender", required: false }], notes: ["Usually in the 1st, 3rd or 5th year (odd years)."] });
  add({ code: "karnavedha", name: "Karnavedha (Ear piercing)", aliases: ["ear piercing", "karnavedha", "karna vedha", "chevulu kuttadam", "karnchhedan"],
    nakshatras: N("Ashwini", "Mrigashira", "Punarvasu", "Pushya", "Hasta", "Chitra", "Anuradha", "Shravana", "Dhanishta", "Revati"), period: "morning", personal_roles: ["child"], requirements: [...CHILD, ...COMMON] });
  add({ code: "aksharabhyasam", name: "Aksharabhyasam / Vidyarambha (Start of learning)", aliases: ["aksharabhyasam", "vidyarambha", "vidyarambham", "start of education", "akshar abhyas", "school start", "patti pooja", "hate khori"],
    nakshatras: N("Ashwini", "Punarvasu", "Pushya", "Hasta", "Chitra", "Swati", "Shravana", "Dhanishta", "Shatabhisha", "Revati", "Mrigashira", "Ardra", "Moola", "Purva Phalguni", "Purva Ashadha", "Purva Bhadrapada", "Anuradha"),
    best_nakshatras: N("Shravana", "Pushya", "Punarvasu", "Hasta", "Revati", "Ashwini"), varas: S(SUN, WED, THU, FRI), ok_varas: S(MON),
    tithi_good_s: S(2, 3, 5, 6, 10, 11, 12), tithi_ok_s: S(7, 13, 15), period: "morning", lagna_pref: "dvi", moudhyam: true, personal_roles: ["child"], swayam_siddha_override: true,
    requirements: [...CHILD, ...COMMON], notes: ["Vasant Panchami and Vijayadashami are especially auspicious."] });
  add({ code: "upanayana", name: "Upanayana (Sacred thread ceremony)", aliases: ["upanayanam", "upanayana", "thread ceremony", "janeu", "munj", "vratabandha", "odugu"],
    nakshatras: U(CHILD_NAK16, N("Purva Phalguni", "Purva Ashadha", "Purva Bhadrapada")), varas: S(SUN, MON, WED, THU, FRI),
    tithi_good_s: S(2, 3, 5, 10, 11, 12), tithi_ok_s: S(7, 13), tithi_good_k: S(2, 3, 5), tithi_ok_k: new Set(), period: "morning", lagna_strict: true, moudhyam: true,
    months: ALLR([MAGHA, PHALGUNA, CHAITRA, VAISHAKHA, JYESHTHA]), avoid_dhanurmasa: true, personal_roles: ["child"], requirements: [...CHILD, ...COMMON], notes: ["Uttarayana and Shukla paksha are strongly preferred."] });
  add({ code: "seemantham", name: "Seemantham / Godh Bharai (Baby shower)", aliases: ["seemantham", "baby shower", "godh bharai", "valaikappu", "dohale jevan", "srimantham", "pumsavana"],
    nakshatras: N("Rohini", "Mrigashira", "Punarvasu", "Pushya", "Hasta", "Moola", "Shravana", "Uttara Phalguni", "Uttara Ashadha", "Uttara Bhadrapada", "Revati", "Anuradha"),
    varas: S(SUN, TUE, THU), ok_varas: S(MON, WED, FRI), period: "morning", personal_roles: ["wife"],
    requirements: [...person("wife", "Mother-to-be"), ...person("husband", "Husband", false), ...COMMON, { key: "pregnancy_month", label: "Current month of pregnancy", required: true }],
    notes: ["Usually done in the 5th, 7th or 9th month of pregnancy (family custom varies)."] });
  add({ code: "pooja", name: "Pooja / Homa / Vratam (Satyanarayana, Ganapati homa, etc.)", aliases: ["pooja", "puja", "homa", "havan", "satyanarayana", "vratam", "abhishekam", "rudrabhishekam", "navagraha", "ganapati homam", "lakshmi pooja", "katha"],
    nakshatras: new Set([...Array(27).keys()]), best_nakshatras: U(DHRUVA, MRIDU, KSHIPRA), varas: S(0, 1, 2, 3, 4, 5, 6),
    tithi_good_s: S(2, 3, 5, 7, 10, 11, 13, 15), tithi_ok_s: S(1, 4, 6, 8, 9, 12, 14), tithi_good_k: S(1, 2, 3, 5, 11), tithi_ok_k: S(4, 6, 7, 8, 9, 10, 12, 13, 14, 15),
    no_adhika: false, avoid_pitru_paksha: false, avoid_bad_yoga: false, avoid_vishti: false,
    requirements: [...person("kartha", "Yajamana (person performing)", false), ...COMMON, { key: "deity", label: "Which pooja / deity", required: true }],
    notes: ["Satyanarayana vratam is best on Purnima, Ekadashi or Sankranti; Shiva poojas suit Pradosha and Masa-shivaratri - the Acharya should mention these."] });
  add({ code: "pratishtha", name: "Devata Pratishtha (Idol installation)", aliases: ["pratishtha", "idol installation", "murti sthapana", "prana pratishtha", "temple"],
    nakshatras: CHILD_NAK16, best_nakshatras: U(DHRUVA, MRIDU, N("Pushya", "Shravana")), lagna_pref: "sthira", lagna_strict: true, moudhyam: true,
    months: ALLR([CHAITRA, VAISHAKHA, JYESHTHA, MAGHA, PHALGUNA]), avoid_dhanurmasa: true,
    requirements: [...person("kartha", "Yajamana / trustee", false), ...COMMON, { key: "deity", label: "Which deity", required: true }] });
  add({ code: "general", name: "General auspicious beginning", aliases: ["auspicious", "good time", "shubh muhurat", "general"],
    nakshatras: U(DHRUVA, MRIDU, KSHIPRA, CHARA_NAK), ok_varas: S(SUN), lagna_pref: "sthira_dvi",
    requirements: [...person("kartha", "Main person", false), ...COMMON, { key: "purpose", label: "What is being started", required: true }] });
  function findEvent(text) {
    const t = String(text || "").trim().toLowerCase();
    if (EVENTS[t]) return EVENTS[t];
    for (const e of Object.values(EVENTS)) if (t === e.name.toLowerCase() || e.aliases.includes(t)) return e;
    for (const e of Object.values(EVENTS)) if (e.aliases.some((a) => t.includes(a)) || e.name.toLowerCase().includes(t)) return e;
    return EVENTS.general;
  }

  // ------------------------------------------------------------------ engine (engine.py)
  const RULE_PROFILE = { telugu: "telugu", marathi: "marathi", north: "north", south_other: "telugu", intl: "telugu" };
  const MALEFICS = ["Sun", "Mars", "Saturn", "Rahu", "Ketu"], BENEFICS = ["Jupiter", "Venus", "Mercury"];
  const DISHA_SHOOLA = { east: S(1, 6), west: S(0, 5), north: S(2, 3), south: S(4) };
  const ENGINE_VERSION = "1.0.0-js";
  const lagnaType = (s) => s % 3;
  const pakshaTithi = (t) => (t < 15 ? [0, t + 1] : [1, t - 14]);
  const tara = (jn, dn) => ((((dn - jn) % 27) + 27) % 27) % 9 + 1;
  const house = (from, to) => ((((to - from) % 12) + 12) % 12) + 1;
  const inAny = (t, ivs) => ivs.some(([a, b]) => a <= t && t < b);
  const uniq = (arr) => [...new Set(arr)];

  function periodBounds(rule, p, profile) {
    const sr = p.sunrise, ss = p.sunset, nsr = p.next_sunrise;
    if (rule.code === "vivaha" && profile === "marathi") return [[sr, ss + 2 / 24]];
    if (rule.period === "any") return [[sr, nsr]];
    if (rule.period === "morning") return [[sr, sr + (ss - sr) / 2 + 1.5 / 24]];
    if (rule.code === "griha_pravesh") return [[sr, ss], [nsr - 2.5 / 24, nsr]];
    return [[sr, ss]];
  }
  function prefBounds(pref, p) {
    if (!pref || pref === "any") return null;
    const tz = p.place.tz;
    const at = (day, h) => { const { y, m, d } = parseISODate(day); const hh = Math.floor(h), mm = Math.round((h - hh) * 60); return localToUt(y, m, d, hh, mm, tz); };
    const d = p.date, d1 = addDays(p.date, 1);
    return ({ predawn: [[at(d1, 3), p.next_sunrise]], morning: [[p.sunrise, at(d, 12)]], afternoon: [[at(d, 12), at(d, 16)]],
      evening: [[at(d, 16), at(d, 20.5)]], night: [[at(d, 19), at(d1, 5)]], daytime: [[p.sunrise, p.sunset]] })[pref] || null;
  }
  function intersect(a, b) {
    if (!b) return a; const out = [];
    for (const [x0, x1] of a) for (const [y0, y1] of b) { const lo = Math.max(x0, y0), hi = Math.min(x1, y1); if (hi > lo) out.push([lo, hi]); }
    return out;
  }
  function dayChecks(rule, p, profile, q, eclipses) {
    const good = [], caut = []; let delta = 0;
    const masa = p.masa, tSr = p.at(p.tithis, p.sunrise); const [paksha, tnum] = pakshaTithi(tSr); const mname = L.MASA.en[masa];
    if (rule.no_adhika && p.adhika) return [false, [], [`Adhika ${mname} masa - not used for this event`], 0];
    if (rule.months) {
      const allowed = rule.months[profile] || rule.months.telugu;
      if (!allowed.has(masa)) return [false, [], [`${mname} masa is not used for ${rule.name} in this tradition`], 0];
      if (rule.ok_months && (rule.ok_months[profile] || new Set()).has(masa)) { delta -= 5; caut.push(`${mname} masa is acceptable, not the best month`); }
      else good.push(`${mname} masa is favourable`);
    }
    if (rule.avoid_dhanurmasa) {
      if (p.sun_rashi === 8) return [false, [], ["Dhanurmasa (Sun in Dhanu) - auspicious ceremonies are avoided"], 0];
      if (profile === "north" && p.sun_rashi === 11) return [false, [], ["Kharmas (Sun in Meena) - auspicious ceremonies are avoided"], 0];
    }
    if (rule.avoid_chaturmasa && rule.avoid_chaturmasa[profile]) {
      const ti = tSr;
      if ((masa === ASHADHA && ti >= 10) || [SHRAVANA, BHADRAPADA, ASHWAYUJA].includes(masa) || (masa === KARTIKA && ti < 10))
        return [false, [], ["Chaturmasa - weddings and similar ceremonies are avoided"], 0];
    }
    if (rule.avoid_pitru_paksha && masa === BHADRAPADA && tSr >= 15) return [false, [], ["Pitru Paksha (Mahalaya) - new beginnings are avoided"], 0];
    if (profile === "north" && ["vivaha", "griha_pravesh", "nischitartham", "vyapara"].includes(rule.code) && masa === PHALGUNA && tSr >= 7 && tSr <= 14)
      return [false, [], ["Holashtak - auspicious ceremonies are avoided"], 0];
    if (rule.moudhyam) {
      if (p.guru_moudhyam) return [false, [], ["Guru moudhyam (Jupiter combust) - this event is not performed"], 0];
      if (p.shukra_moudhyam) return [false, [], ["Shukra moudhyam (Venus combust) - this event is not performed"], 0];
      good.push("Guru and Shukra are both strong (no moudhyam)");
    }
    if (rule.code !== "pooja") for (const [kind, peak] of eclipses) if (p.sunrise - 0.5 <= peak && peak <= p.next_sunrise) return [false, [], [`${kind[0].toUpperCase() + kind.slice(1)} eclipse day - avoided`], 0];
    const ss = SWAYAM[`${masa},${paksha},${tnum}`];
    if (ss) { delta += 8; good.push(`${ss} - a swayam-siddha (self-auspicious) day`); }
    if (rule.code === "annaprashana") {
      const child = q.persons.find((x) => x.role === "child" && x.dob);
      if (child) {
        const a = parseISODate(p.date), b = parseISODate(child.dob);
        const months = (a.y - b.y) * 12 + (a.m - b.m) - (a.d < b.d ? 1 : 0); const g = String(child.gender || "").toLowerCase()[0];
        if (months < 5) return [false, [], ["Child is younger than 5 months"], 0];
        if (g === "m" && months % 2 === 1) { delta -= 10; caut.push(`Child will be ${months} months - boys usually in even months (6, 8)`); }
        else if (g === "f" && months % 2 === 0) { delta -= 10; caut.push(`Child will be ${months} months - girls usually in odd months (5, 7)`); }
        else good.push(`Child's age (${months} months) suits annaprashana`);
      }
    }
    if (rule.code === "vivaha") {
      const jup = Math.floor(sid("Jupiter", p.sunrise) / 30);
      const bride = q.persons.find((x) => x.role === "bride" && x.janma), groom = q.persons.find((x) => x.role === "groom" && x.janma);
      if (bride) { const h = house(bride.janma.rashi, jup); if ([2, 5, 7, 9, 11].includes(h)) { delta += 4; good.push("Guru bala for the bride is strong"); } else if ([4, 8, 12].includes(h)) { delta -= 6; caut.push("Guru bala for the bride is weak - pandit may advise Guru shanti"); } }
      if (groom) { const h = house(groom.janma.rashi, p.sun_rashi); if ([3, 6, 10, 11].includes(h)) { delta += 3; good.push("Surya bala for the groom is strong"); } else if ([4, 8, 12].includes(h)) { delta -= 4; caut.push("Surya bala for the groom is weak"); } }
    }
    return [true, good, caut, delta];
  }
  function evalSlice(rule, p, t, profile, q, swayam, tl) {
    const good = [], caut = []; let score = 50;
    const tithi = spanAt(tl.tithi, t), nak = spanAt(tl.nakshatra, t), yoga = spanAt(tl.yoga, t), kar = spanAt(tl.karana, t), lag = spanAt(tl.lagna, t), vara = p.vara;
    const info = { tithi, nakshatra: nak, yoga, karana: kar, lagna: lag, vara };
    const [paksha, tnum] = pakshaTithi(tithi); const nakName = L.NAKSHATRA.en[nak];
    const no = (r) => [false, 0, [], [r], info];
    if (t < p.sunset) {
      if (p.rahu[0] <= t && t < p.rahu[1]) return no("Rahu Kalam");
      if (p.yamaganda[0] <= t && t < p.yamaganda[1]) { if (profile === "telugu") return no("Yamagandam"); score -= 5; caut.push("Overlaps Yamagandam (not strictly observed in this tradition)"); }
      if (p.gulika[0] <= t && t < p.gulika[1] && rule.code !== "pooja") { score -= 4; caut.push("Overlaps Gulika Kalam - minor"); }
    }
    if (inAny(t, p.durmuhurtas)) return no("Durmuhurtham");
    if (inAny(t, tl.varjyam)) return no("Varjyam");
    if (rule.varas.has(vara)) score += 5;
    else if (rule.ok_varas.has(vara)) { score -= 6; caut.push(`${L.VARA.en[vara]} is acceptable but not ideal`); }
    else return no(`${L.VARA.en[vara]} not used for this event`);
    if (rule.nakshatras.has(nak)) {
      if (rule.best_nakshatras.has(nak)) { score += 8; good.push(`${nakName} nakshatra - among the best for ${rule.name}`); } else good.push(`${nakName} nakshatra is suitable`);
    } else if (swayam && rule.swayam_siddha_override) caut.push(`${nakName} nakshatra accepted because the day itself is swayam-siddha`);
    else return no(`${nakName} nakshatra not suitable`);
    const [gs, os] = paksha === 0 ? [rule.tithi_good_s, rule.tithi_ok_s] : [rule.tithi_good_k, rule.tithi_ok_k];
    const tname = `${L.PAKSHA.en[paksha]} ${L.TITHI.en[tnum < 15 ? tnum - 1 : paksha === 0 ? 14 : 15]}`;
    if (gs.has(tnum)) { score += 6; good.push(`${tname} is a good tithi`); }
    else if (os.has(tnum)) { if (paksha === 1 && tnum >= 7) { score -= 3; caut.push(`${tname} - waning moon, acceptable`); } }
    else if (!(swayam && rule.swayam_siddha_override)) return no(`${tname} not suitable`);
    if (WORST_YOGAS.has(yoga) && rule.code !== "pooja") return no(`${L.YOGA_EN[yoga]} yoga`);
    if (BAD_YOGAS.has(yoga)) { if (rule.avoid_bad_yoga) return no(`${L.YOGA_EN[yoga]} yoga`); score -= 4; } else score += 2;
    if (kar === 7) { if (rule.avoid_vishti) return no("Vishti (Bhadra) karana"); score -= 5; caut.push("Vishti karana - minor"); }
    if ((SARVARTHA[vara] || new Set()).has(nak)) { score += 6; good.push("Sarvartha Siddhi yoga (weekday + star combination)"); }
    if (nak === 7 && (vara === 0 || vara === 4) && ["jewellery_purchase", "vehicle_purchase", "property_purchase", "vyapara", "aksharabhyasam", "pooja"].includes(rule.code)) { score += 6; good.push("Guru Pushya / Ravi Pushya yoga"); }
    if (rule.code === "yatra" && q.direction) {
      const dirn = String(q.direction).toLowerCase().trim();
      if ((DISHA_SHOOLA[dirn] || new Set()).has(vara)) return no(`Disha shoola - ${dirn} travel avoided on ${L.VARA.en[vara]}`);
      if (dirn === "south" && moon(t) >= 300) return no("Panchaka - southward travel avoided");
    }
    if (rule.code === "bhoomi_puja" && moon(t) >= 300) { score -= 6; caut.push("Panchaka period - minor caution for construction"); }
    const moonRashi = Math.floor(moon(t) / 30);
    for (const pr of q.persons) {
      if (!rule.personal_roles.includes(pr.role) || !pr.janma) continue;
      const who = pr.name || pr.role;
      const count = ((((nak - pr.janma.nakshatra) % 27) + 27) % 27) + 1; const tr = ((count - 1) % 9) + 1;
      if (count === 1 && ["vivaha", "upanayana", "nischitartham"].includes(rule.code)) return no(`Janma nakshatra of ${who} - own birth-star day is avoided`);
      if ([3, 5, 7].includes(tr)) { if (paksha === 1) return no(`Tarabalam unfavourable for ${who} (${L.TARA_EN[tr - 1]} tara)`); score -= 5; caut.push(`Tarabalam weak for ${who} (${L.TARA_EN[tr - 1]} tara) - chandrabalam governs in Shukla paksha`); }
      else if (tr === 1) { score -= 4; caut.push(`Janma-group tara for ${who}`); }
      else { score += 3; good.push(`Tarabalam good for ${who} (${L.TARA_EN[tr - 1]} tara)`); }
      const ch = house(pr.janma.rashi, moonRashi);
      if ([4, 8, 12].includes(ch)) { if (paksha === 0) return no(`Chandrabalam unfavourable for ${who} (Moon ${ch}th from janma rashi)`); score -= 5; caut.push(`Chandrabalam weak for ${who} - tarabalam governs in Krishna paksha`); }
      else if ([1, 3, 6, 7, 10, 11].includes(ch)) { score += 3; good.push(`Chandrabalam good for ${who}`); }
      else if (paksha === 1) score -= 2;
      const lh = house(pr.janma.rashi, lag);
      if (lh === 8) return no(`Lagna is 8th from ${who}'s janma rashi (janma-ashtama)`);
      if (lh === 12) score -= 3;
      if (!pr.janma.certain) caut.push(`${who}'s birth star is uncertain (birth time not given)`);
    }
    const lt = lagnaType(lag), pref = rule.lagna_pref, lname = L.RASHI.en[lag];
    if (pref === "sthira") { if (lt === 1) { score += 8; good.push(`${lname} lagna - sthira (fixed), ideal for permanence`); } else if (lt === 2) score += 2; else { score -= 12; caut.push(`${lname} lagna is chara (movable); sthira is preferred`); } }
    else if (pref === "chara") { if (lt === 0) { score += 8; good.push(`${lname} lagna - chara (movable), ideal for vehicles and travel`); } else if (lt === 2) score += 3; }
    else if (pref === "dvi") { if (lt === 2) { score += 6; good.push(`${lname} lagna - dvisvabhava, ideal for learning`); } }
    else if (pref === "sthira_dvi") { if (lt === 1 || lt === 2) { score += 5; good.push(`${lname} lagna is steady`); } }
    const pl = allPlanets(t); const hs = {}; for (const k of PLANETS) hs[k] = house(lag, Math.floor(pl[k] / 30));
    const bad8 = MALEFICS.filter((x) => hs[x] === 8); if (bad8.length) return no(`Lagna shuddhi: ${bad8.join(", ")} in the 8th house`);
    if ((rule.lagna_strict ? [6, 8, 12] : [8]).includes(hs.Moon)) return no(`Lagna shuddhi: Moon in the ${hs.Moon}th house`);
    if (rule.lagna_strict) {
      const bad7 = MALEFICS.filter((x) => hs[x] === 7); if (bad7.length) return no(`Lagna shuddhi: ${bad7.join(", ")} in the 7th house`);
      if (rule.code === "vivaha" && hs.Venus === 6) return no("Lagna shuddhi: Venus in the 6th house");
      good.push("Lagna shuddhi is clean (7th and 8th houses free of malefics)");
    } else good.push("8th house from lagna is clean");
    for (const b of BENEFICS) {
      if ([1, 4, 7, 10].includes(hs[b])) { score += b === "Jupiter" ? 3 : 2; good.push(`${b} in a kendra from lagna`); }
      else if ([5, 9].includes(hs[b]) && b === "Jupiter") { score += 2; good.push("Jupiter in a trikona from lagna"); }
    }
    if (p.abhijit[0] <= t && t < p.abhijit[1] && vara !== 3) { score += 4; good.push("Abhijit muhurtham"); }
    if (inAny(t, tl.amrita)) { score += 5; good.push("Amrita kalam"); }
    return [true, score, good, caut, info];
  }
  function timeline(days) {
    const merge = (attr) => { const seen = new Set(), out = []; for (const p of days) for (const s of p[attr]) { const k = s.index + "|" + s.start.toFixed(4); if (!seen.has(k)) { seen.add(k); out.push(s); } } return out.sort((a, b) => a.start - b.start); };
    const mergeIv = (attr) => { const seen = new Set(), out = []; for (const p of days) for (const [a, b] of p[attr]) { const k = a.toFixed(6) + "|" + b.toFixed(6); if (!seen.has(k)) { seen.add(k); out.push([a, b]); } } return out.sort((x, y) => x[0] - y[0]); };
    return { tithi: merge("tithis"), nakshatra: merge("nakshatras"), yoga: merge("yogas"), karana: merge("karanas"), lagna: merge("lagnas"), varjyam: mergeIv("varjyams"), amrita: mergeIv("amritas") };
  }
  function quality(s) { return s >= 85 ? "uttama" : s >= 72 ? "shubha" : s >= 60 ? "madhyama" : "adhama"; }
  function windowToDict(w, q, n) {
    const tz = q.place.tz, lang = q.lang; const p = dayPanchang(w.hindu_day, q.place);
    const [paksha, tnum] = pakshaTithi(w.tithi); const tidx = tnum < 15 ? tnum - 1 : paksha === 0 ? 14 : 15;
    let masaIdx = p.masa; if (RULE_PROFILE[q.region] === "north" && paksha === 1) masaIdx = (masaIdx + 1) % 12;
    const sp = utParts(w.start, tz);
    return {
      option_id: `opt-${w.hindu_day}-${pad(sp.H)}${pad(sp.M)}`, rank_in_window: n, date: civilDate(w.start, tz),
      weekday: nm(L.VARA, weekdayOf(civilDate(w.start, tz)), lang), hindu_vara: nm(L.VARA, w.vara, lang),
      start: fmt(w.start, tz), end: fmt(w.end, tz), start_time: hm12(w.start, tz), end_time: hm12(w.end, tz),
      duration_minutes: Math.round((w.end - w.start) * 1440), score: Math.round(w.score * 10) / 10, quality: quality(w.score),
      panchang: {
        samvatsara: L.SAMVATSARA_EN[p.samvatsara], masa: (p.adhika ? "Adhika " : "") + nm(L.MASA, masaIdx, lang), paksha: nm(L.PAKSHA, paksha, lang),
        tithi: nm(L.TITHI, tidx, lang), nakshatra: nm(L.NAKSHATRA, w.nakshatra, lang), yoga: L.YOGA_EN[w.yoga], karana: L.KARANA_EN[w.karana],
        lagna: nm(L.RASHI, w.lagna, lang), lagna_type: L.LAGNA_TYPE_EN[lagnaType(w.lagna)], sunrise: hm(p.sunrise, tz), sunset: hm(p.sunset, tz), rahu_kalam: p.rahu.map((x) => hm(x, tz)),
      },
      why_good: w.good.slice(0, 10), cautions: w.caution.slice(0, 6),
    };
  }
  function search(q) {
    const rule = findEvent(q.event); const profile = RULE_PROFILE[q.region] || "telugu";
    const span = daysBetween(q.start, q.end);
    if (span > 400) throw new Error("Date window too long - please keep it within about a year");
    if (span < 0) throw new Error("End date is before start date");
    const dates = []; for (let i = -1; i <= span; i++) dates.push(addDays(q.start, i));
    const days = dates.map((d) => dayPanchang(d, q.place)); const tl = timeline(days);
    const eclipses = eclipsesBetween(Math.round(days[0].sunrise * 100) / 100, Math.round((days[days.length - 1].next_sunrise + 1) * 100) / 100, Math.round(q.place.lat * 1000) / 1000, Math.round(q.place.lon * 1000) / 1000);
    const avoid = new Set(q.avoid_dates || []); const windows = []; const rejected = {};
    for (const p of days.slice(1)) {
      if (avoid.has(p.date)) { rejected[p.date] = "Family not available"; continue; }
      const [ok, dgood, dcaut, ddelta] = dayChecks(rule, p, profile, q, eclipses);
      if (!ok) { rejected[p.date] = dcaut[0] || "Not suitable"; continue; }
      const tSr = p.at(p.tithis, p.sunrise); const swayam = !!SWAYAM[`${p.masa},${pakshaTithi(tSr).join(",")}`];
      for (const [b0, b1] of intersect(periodBounds(rule, p, profile), prefBounds(q.time_pref, p))) {
        const cutsSet = new Set([b0, b1]);
        for (const key of ["tithi", "nakshatra", "yoga", "karana", "lagna"]) for (const s of tl[key]) for (const x of [s.start, s.end]) if (b0 < x && x < b1) cutsSet.add(x);
        for (const [a, b] of [p.rahu, p.yamaganda, p.gulika, p.abhijit, ...p.durmuhurtas, ...tl.varjyam, ...tl.amrita]) for (const x of [a, b]) if (b0 < x && x < b1) cutsSet.add(x);
        const cuts = [...cutsSet].sort((x, y) => x - y); let cur = null;
        for (let i = 0; i + 1 < cuts.length; i++) {
          const a = cuts[i], b = cuts[i + 1]; if (b - a < 30 / 86400) continue;
          const mid = (a + b) / 2; const civ = civilDate(mid, q.place.tz);
          let res;
          if (q.weekdays && !q.weekdays.has(weekdayOf(civ))) res = [false];
          else if (avoid.has(civ)) res = [false];
          else res = evalSlice(rule, p, mid, profile, q, swayam, tl);
          if (res[0]) {
            let [, sc, g, c, info] = res; sc += ddelta;
            if (cur && Math.abs(cur.end - a) < 60 / 86400 && cur.lagna === info.lagna) { cur.end = b; if (sc < cur.score) cur.score = sc; cur.good = uniq(cur.good.concat(g)); cur.caution = uniq(cur.caution.concat(c)); }
            else { if (cur) windows.push(cur); cur = { start: a, end: b, score: sc, hindu_day: p.date, lagna: info.lagna, tithi: info.tithi, nakshatra: info.nakshatra, yoga: info.yoga, karana: info.karana, vara: info.vara, good: uniq(dgood.concat(g)), caution: uniq(dcaut.concat(c)) }; }
          } else { if (cur) windows.push(cur); cur = null; }
        }
        if (cur) windows.push(cur);
      }
    }
    const ws = windows.filter((w) => (w.end - w.start) * 1440 >= rule.min_minutes);
    for (const w of ws) { const mins = (w.end - w.start) * 1440; w.score += Math.min(4, Math.max(0, (mins - 30) / 15)); w.score = Math.max(0, Math.min(100, w.score)); }
    const best = {};
    for (const w of ws) { const c = best[w.hindu_day]; if (!c || w.score > c.score || (w.score === c.score && w.end - w.start > c.end - c.start)) best[w.hindu_day] = w; }
    const ranked = Object.values(best).sort((a, b) => b.score - a.score || a.start - b.start);
    const chosen = ranked.slice(0, Math.max(1, q.options || 3)).sort((a, b) => a.start - b.start);
    return {
      engine_version: ENGINE_VERSION, event: { code: rule.code, name: rule.name }, tradition: profile,
      place: { name: q.place.name, lat: q.place.lat, lon: q.place.lon, tz: q.place.tz }, window: { from: q.start, to: q.end },
      personalised: q.persons.some((x) => x.janma && rule.personal_roles.includes(x.role)),
      options: chosen.map((w, i) => windowToDict(w, q, i + 1)), candidate_days: Object.keys(best).length,
      rejected_days_sample: Object.fromEntries(Object.entries(rejected).slice(0, 15)), rule_notes: rule.notes,
    };
  }

  // ------------------------------------------------------------------ places (places.py)
  const IN = "Asia/Kolkata";
  const CITIES = {
    hyderabad: [17.385, 78.4867, IN, "telugu"], secunderabad: [17.4399, 78.4983, IN, "telugu"], warangal: [17.9689, 79.5941, IN, "telugu"], karimnagar: [18.4386, 79.1288, IN, "telugu"],
    nizamabad: [18.6725, 78.0941, IN, "telugu"], khammam: [17.2473, 80.1514, IN, "telugu"], nalgonda: [17.0575, 79.2671, IN, "telugu"], mahbubnagar: [16.7488, 77.9855, IN, "telugu"],
    adilabad: [19.6641, 78.532, IN, "telugu"], siddipet: [18.1018, 78.852, IN, "telugu"], vijayawada: [16.5062, 80.648, IN, "telugu"], visakhapatnam: [17.6868, 83.2185, IN, "telugu"],
    vizag: [17.6868, 83.2185, IN, "telugu"], guntur: [16.3067, 80.4365, IN, "telugu"], tirupati: [13.6288, 79.4192, IN, "telugu"], nellore: [14.4426, 79.9865, IN, "telugu"],
    kurnool: [15.8281, 78.0373, IN, "telugu"], rajahmundry: [17.0005, 81.804, IN, "telugu"], rajamahendravaram: [17.0005, 81.804, IN, "telugu"], kakinada: [16.9891, 82.2475, IN, "telugu"],
    anantapur: [14.6819, 77.6006, IN, "telugu"], kadapa: [14.4673, 78.8242, IN, "telugu"], eluru: [16.7107, 81.0952, IN, "telugu"], ongole: [15.5057, 80.0499, IN, "telugu"],
    srikakulam: [18.2949, 83.8938, IN, "telugu"], vizianagaram: [18.1067, 83.3956, IN, "telugu"], amaravati: [16.5131, 80.5165, IN, "telugu"], bhadrachalam: [17.6688, 80.8936, IN, "telugu"],
    mumbai: [19.076, 72.8777, IN, "marathi"], bombay: [19.076, 72.8777, IN, "marathi"], thane: [19.2183, 72.9781, IN, "marathi"], "navi mumbai": [19.033, 73.0297, IN, "marathi"],
    pune: [18.5204, 73.8567, IN, "marathi"], nagpur: [21.1458, 79.0882, IN, "marathi"], nashik: [19.9975, 73.7898, IN, "marathi"], aurangabad: [19.8762, 75.3433, IN, "marathi"],
    "chhatrapati sambhajinagar": [19.8762, 75.3433, IN, "marathi"], solapur: [17.6599, 75.9064, IN, "marathi"], kolhapur: [16.705, 74.2433, IN, "marathi"], amravati: [20.9374, 77.7796, IN, "marathi"],
    nanded: [19.1383, 77.321, IN, "marathi"], sangli: [16.8524, 74.5815, IN, "marathi"], latur: [18.4088, 76.5604, IN, "marathi"], ahmednagar: [19.0948, 74.748, IN, "marathi"],
    kalyan: [19.2403, 73.1305, IN, "marathi"], vasai: [19.3919, 72.8397, IN, "marathi"], satara: [17.6805, 74.0183, IN, "marathi"], ratnagiri: [16.9902, 73.312, IN, "marathi"],
    panaji: [15.4909, 73.8278, IN, "marathi"], goa: [15.4909, 73.8278, IN, "marathi"],
    bengaluru: [12.9716, 77.5946, IN, "south_other"], bangalore: [12.9716, 77.5946, IN, "south_other"], chennai: [13.0827, 80.2707, IN, "south_other"], mysuru: [12.2958, 76.6394, IN, "south_other"],
    mysore: [12.2958, 76.6394, IN, "south_other"], coimbatore: [11.0168, 76.9558, IN, "south_other"], madurai: [9.9252, 78.1198, IN, "south_other"], kochi: [9.9312, 76.2673, IN, "south_other"],
    thiruvananthapuram: [8.5241, 76.9366, IN, "south_other"], mangaluru: [12.9141, 74.856, IN, "south_other"], hubli: [15.3647, 75.124, IN, "south_other"], belagavi: [15.8497, 74.4977, IN, "marathi"],
    delhi: [28.6139, 77.209, IN, "north"], "new delhi": [28.6139, 77.209, IN, "north"], noida: [28.5355, 77.391, IN, "north"], gurugram: [28.4595, 77.0266, IN, "north"],
    gurgaon: [28.4595, 77.0266, IN, "north"], jaipur: [26.9124, 75.7873, IN, "north"], lucknow: [26.8467, 80.9462, IN, "north"], kanpur: [26.4499, 80.3319, IN, "north"],
    varanasi: [25.3176, 82.9739, IN, "north"], prayagraj: [25.4358, 81.8463, IN, "north"], allahabad: [25.4358, 81.8463, IN, "north"], agra: [27.1767, 78.0081, IN, "north"],
    patna: [25.5941, 85.1376, IN, "north"], bhopal: [23.2599, 77.4126, IN, "north"], indore: [22.7196, 75.8577, IN, "north"], chandigarh: [30.7333, 76.7794, IN, "north"],
    dehradun: [30.3165, 78.0322, IN, "north"], haridwar: [29.9457, 78.1642, IN, "north"], ayodhya: [26.7922, 82.1998, IN, "north"], mathura: [27.4924, 77.6737, IN, "north"],
    raipur: [21.2514, 81.6296, IN, "north"], ranchi: [23.3441, 85.3096, IN, "north"], ahmedabad: [23.0225, 72.5714, IN, "north"], surat: [21.1702, 72.8311, IN, "north"],
    vadodara: [22.3072, 73.1812, IN, "north"], kolkata: [22.5726, 88.3639, IN, "north"], bhubaneswar: [20.2961, 85.8245, IN, "north"], guwahati: [26.1445, 91.7362, IN, "north"],
    dubai: [25.2048, 55.2708, "Asia/Dubai", "intl"], singapore: [1.3521, 103.8198, "Asia/Singapore", "intl"], london: [51.5074, -0.1278, "Europe/London", "intl"],
    "new york": [40.7128, -74.006, "America/New_York", "intl"], "new jersey": [40.0583, -74.4057, "America/New_York", "intl"], chicago: [41.8781, -87.6298, "America/Chicago", "intl"],
    dallas: [32.7767, -96.797, "America/Chicago", "intl"], houston: [29.7604, -95.3698, "America/Chicago", "intl"], "san francisco": [37.7749, -122.4194, "America/Los_Angeles", "intl"],
    "san jose": [37.3382, -121.8863, "America/Los_Angeles", "intl"], seattle: [47.6062, -122.3321, "America/Los_Angeles", "intl"], atlanta: [33.749, -84.388, "America/New_York", "intl"],
    toronto: [43.6532, -79.3832, "America/Toronto", "intl"], sydney: [-33.8688, 151.2093, "Australia/Sydney", "intl"], melbourne: [-37.8136, 144.9631, "Australia/Melbourne", "intl"],
  };
  const title = (s) => s.replace(/\b\w/g, (c) => c.toUpperCase());
  function cityKey(s) { let k = String(s || "").normalize("NFKC").toLowerCase().trim(); for (const j of [",", ".", " india", " city", " district"]) k = k.split(j).join(" "); return k.split(/\s+/).filter(Boolean).join(" "); }
  function resolvePlace(spec) {
    if (spec && typeof spec === "object" && spec.lat != null && spec.lon != null) {
      const tz = spec.tz || IN; return { place: { lat: +spec.lat, lon: +spec.lon, tz, name: spec.name || `${spec.lat}, ${spec.lon}` }, region: spec.region || "telugu" };
    }
    const k = cityKey(typeof spec === "object" ? spec && (spec.name || spec.city) : spec);
    if (!k) return null;
    const hit = CITIES[k] ? k : Object.keys(CITIES).find((c) => k.includes(c) || c.includes(k));
    if (!hit) return null;
    const [lat, lon, tz, region] = CITIES[hit];
    return { place: { lat, lon, tz, name: title(hit) }, region };
  }
  function placeCandidates(q) {
    const k = cityKey(q); if (!k) return [];
    const hits = CITIES[k] ? [k] : Object.keys(CITIES).filter((c) => k.includes(c) || c.includes(k)).slice(0, 5);
    return hits.map((c) => ({ name: title(c), lat: CITIES[c][0], lon: CITIES[c][1], tz: CITIES[c][2], region: CITIES[c][3] }));
  }

  // ------------------------------------------------------------------ service (service.py)
  class InputError extends Error {}
  const MONTHS = { jan: 1, feb: 2, mar: 3, apr: 4, may: 5, jun: 6, jul: 7, aug: 8, sep: 9, oct: 10, nov: 11, dec: 12 };
  function parseDate(s) {
    s = String(s || "").trim(); let m;
    if ((m = s.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/))) return `${m[1]}-${pad(+m[2])}-${pad(+m[3])}`;
    if ((m = s.match(/^(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})$/))) return `${m[3]}-${pad(+m[2])}-${pad(+m[1])}`;
    if ((m = s.match(/^(\d{1,2})\s+([A-Za-z]{3})[a-z]*\s+(\d{4})$/)) && MONTHS[m[2].toLowerCase()]) return `${m[3]}-${pad(MONTHS[m[2].toLowerCase()])}-${pad(+m[1])}`;
    throw new InputError(`Could not read the date '${s}'. Use YYYY-MM-DD.`);
  }
  function parseTime(s) {
    if (!s) return null; s = String(s).trim().toUpperCase().replace(".", ":"); let m;
    if ((m = s.match(/^(\d{1,2}):(\d{2})(?::\d{2})?$/))) return `${pad(+m[1])}:${m[2]}`;
    if ((m = s.match(/^(\d{1,2})(?::(\d{2}))?\s*(AM|PM)$/))) { let h = +m[1] % 12; if (m[3] === "PM") h += 12; return `${pad(h)}:${m[2] || "00"}`; }
    throw new InputError(`Could not read the time '${s}'. Use HH:MM (24h) or 10:30 AM.`);
  }
  function placeFrom(spec) { const r = resolvePlace(spec); if (!r) throw new InputError(`Place '${typeof spec === "object" ? JSON.stringify(spec) : spec}' not found. Give the nearest big city.`); return r; }
  function personFrom(d) {
    const role = String(d.role || "kartha").toLowerCase(); const name = d.name || ""; const gender = d.gender || null;
    const dob = d.dob ? parseDate(d.dob) : null; let janma = null;
    if (d.nakshatra || d.rashi) {
      const ni = d.nakshatra ? nakIndexFromName(d.nakshatra) : null; let ri = d.rashi ? rashiIndexFromName(d.rashi) : null;
      if (ni === null) throw new InputError(`Janma nakshatra needed (could not read '${d.nakshatra}')`);
      if (d.rashi && ri === null) throw new InputError(`Unknown rashi '${d.rashi}'`);
      const pada = +(d.pada || 0);
      if (ri === null) ri = pada ? Math.floor(((ni * 4 + pada - 1) * (40 / 12)) / 30) : Math.floor((ni * (40 / 3) + 0.01) / 30);
      janma = { nakshatra: ni, pada: pada || 1, rashi: ri, certain: !!(d.rashi || pada), note: d.rashi || pada ? "" : "Rashi inferred from nakshatra; confirm with family" };
    } else if (dob) {
      const bp = d.birthplace || d.birth_place; if (!bp) throw new InputError(`Birth place needed for ${name || role}`);
      janma = janmaFromBirth(dob, parseTime(d.tob || d.birth_time), placeFrom(bp).place);
    }
    return { role, name, janma, gender, dob };
  }
  function janmaSummary(p, lang = "en") {
    if (!p.janma) return { role: p.role, name: p.name, available: false };
    const j = p.janma;
    return { role: p.role, name: p.name, available: true, nakshatra: nm(L.NAKSHATRA, j.nakshatra, lang), pada: j.pada, rashi: nm(L.RASHI, j.rashi, lang),
      nakshatra_en: L.NAKSHATRA.en[j.nakshatra], rashi_en: L.RASHI.en[j.rashi], certain: j.certain, note: j.note };
  }
  function eventRequirements(ev) {
    const e = findEvent(ev);
    return { code: e.code, name: e.name, whose_stars_are_checked: e.personal_roles, requirements: e.requirements, notes: e.notes,
      matched: e.code !== "general" || ["general", "auspicious"].includes(String(ev).toLowerCase().trim()) };
  }
  function findMuhurtham(a) {
    const start = parseDate(a.from_date), end = parseDate(a.to_date);
    if (daysBetween(todayIn(), start) < -1) throw new InputError("The start date is in the past");
    if (daysBetween(start, end) > (a.max_window_days || 366)) throw new InputError(`Please keep the date range within ${a.max_window_days || 366} days`);
    const r = placeFrom(a.venue); let region = r.region;
    if (a.tradition) region = { telugu: "telugu", marathi: "marathi", north: "north", hindi: "north", south: "telugu" }[String(a.tradition).toLowerCase()] || region;
    const ppl = (a.persons || []).map((p) => (p.janma !== undefined && p.role ? p : personFrom(p)));
    let wd = null;
    if (a.weekdays && a.weekdays.length) { const names = L.VARA.en.map((v) => v.toLowerCase()); const s = new Set(a.weekdays.map((w) => names.indexOf(String(w).toLowerCase())).filter((i) => i >= 0)); wd = s.size ? s : null; }
    const q = { event: a.event, start, end, place: r.place, region, persons: ppl, time_pref: String(a.time_pref || "any").toLowerCase(), weekdays: wd,
      avoid_dates: (a.avoid_dates || []).map(parseDate), direction: a.direction || null, options: Math.max(1, Math.min(+(a.options || 3), 5)), lang: a.lang || "en" };
    const res = search(q); res.people = ppl.map((p) => janmaSummary(p, q.lang)); return res;
  }
  function panchangFor(date, venue, lang = "en") { return panchangDict(dayPanchang(parseDate(date), placeFrom(venue).place), lang); }

  const API = { L, EVENTS, findEvent, eventRequirements, findMuhurtham, panchangFor, personFrom, janmaSummary, placeCandidates, resolvePlace, todayIn,
    search, dayPanchang, panchangDict, janmaFromBirth, InputError, ENGINE_VERSION, _internal: { sun, moon, trueAyanamsa, ascendant, eclipsesBetween, msToUt, utToMs, fmt } };
  if (typeof module !== "undefined" && module.exports) module.exports = API; else root.KaamyaEngine = API;
})(typeof globalThis !== "undefined" ? globalThis : this);
