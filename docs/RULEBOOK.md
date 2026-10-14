# Kaamya Muhurtha - Rule Book (for senior pandit review)

Generated from the engine's own rule tables. Every line is a rule the engine applies.
Please mark changes in the margin; Vinay/Claude will update `app/rules/events.py` and regenerate.

## 1. Calculation standard

- Drik-ganita (modern astronomical) positions, geocentric, true-of-date.
- Ayanamsa: Lahiri (Chitrapaksha). Verified against published panchangams to within 1 minute.
- Months: amanta (Telugu & Marathi). North (Hindi) tradition shows purnimanta month names.
- Hindu day (vara) runs sunrise to next sunrise. A 4:30 am muhurtham on Friday belongs to Thursday's vara.
- Sunrise/sunset: upper limb of the Sun with standard refraction, at the venue.

## 2. Rules applied to every auspicious event

| Check | Rule |
|---|---|
| Rahu Kalam | never (day divided in 8; part by weekday Sun..Sat = [8, 2, 7, 5, 6, 4, 3]) |
| Yamagandam | never in Telugu tradition; small penalty elsewhere (parts [5, 4, 3, 2, 1, 7, 6]) |
| Gulika Kalam | small penalty (parts [7, 6, 5, 4, 3, 2, 1]) |
| Durmuhurtham | never (day muhurtas of 15 by weekday [[14], [9, 12], [4], [8], [6, 12], [4, 9], [1, 2]]; Tuesday also night 7th) |
| Varjyam (Thyajyam) | never - 4 ghatis starting at the nakshatra's tyajya ghati (table below) |
| Amrita Kalam | bonus |
| Abhijit muhurtham | bonus (not on Wednesday) |
| Bad yogas | avoided: Vishkambha, Atiganda, Shoola, Ganda, Vyaghata, Vajra, Vyatipata, Parigha, Vaidhriti; Vyatipata, Vaidhriti never |
| Vishti (Bhadra) karana | avoided |
| Pitru Paksha (Bhadrapada Krishna) | no new beginnings (except pooja, travel, job, naming) |
| Eclipse day (visible at the venue) | avoided (except pooja) |
| Holashtak (North only) | Phalguna Shukla 8 to Purnima avoided for marriage, griha pravesh, engagement, business |
| Tarabalam | count from janma nakshatra; 3 Vipat, 5 Pratyak, 7 Naidhana are bad |
| Chandrabalam | Moon's rashi 4th, 8th, 12th from janma rashi is bad |
| Which governs | **Shukla paksha: chandrabalam is enforced, tarabalam scored. Krishna paksha: tarabalam enforced, chandrabalam scored.** |
| Janma nakshatra day | not allowed for marriage, engagement, upanayana; small penalty for others |
| Lagna | not 8th from janma rashi (janma-ashtama); 12th is a small penalty |
| Lagna shuddhi (all) | no malefic (Sun, Mars, Saturn, Rahu, Ketu) in 8th; Moon not in 8th |
| Lagna shuddhi (strict events) | also 7th free of malefics, Moon not in 6/8/12; for marriage Venus not in 6th |
| Benefics | Jupiter/Venus/Mercury in kendra, Jupiter in trikona: bonus |
| Moudhyam | Guru within 11 deg of Sun; Shukra within 10 deg (8 deg if retrograde) - forbids marked events |
| Dhanurmasa | Sun in Dhanu: marked events avoided (North also Meena - Kharmas) |
| Chaturmasa | Ashadha Shukla 11 to Kartika Shukla 11 - marked events/regions |

Special bonuses: Sarvartha Siddhi yoga (weekday + star), Guru/Ravi Pushya for purchases, swayam-siddha days: Ugadi / Gudi Padwa (Chaitra Shukla 1), Akshaya Tritiya (Vaishakha Shukla 3), Vijayadashami (Ashwayuja Shukla 10), Bali Pratipada (Kartika Shukla 1), Vasant Panchami (Magha Shukla 5).

### Sarvartha Siddhi yoga table

| Weekday | Nakshatras |
|---|---|
| Sunday | Ashwini, Pushya, Uttara Phalguni, Hasta, Moola, Uttara Ashadha, Uttara Bhadrapada |
| Monday | Rohini, Mrigashira, Pushya, Anuradha, Shravana |
| Tuesday | Ashwini, Krittika, Ashlesha, Uttara Bhadrapada |
| Wednesday | Krittika, Rohini, Mrigashira, Hasta, Anuradha |
| Thursday | Ashwini, Punarvasu, Pushya, Anuradha, Revati |
| Friday | Ashwini, Punarvasu, Anuradha, Shravana, Revati |
| Saturday | Rohini, Swati, Shravana |

### Varjyam and Amrita starting ghati (of 60) per nakshatra

| Nakshatra | Varjyam | Amrita |
|---|---|---|
| Ashwini | 50 | 42 |
| Bharani | 24 | 48 |
| Krittika | 30 | 54 |
| Rohini | 40 | 52 |
| Mrigashira | 14 | 38 |
| Ardra | 11 | 35 |
| Punarvasu | 30 | 54 |
| Pushya | 20 | 44 |
| Ashlesha | 32 | 56 |
| Magha | 30 | 54 |
| Purva Phalguni | 20 | 44 |
| Uttara Phalguni | 18 | 42 |
| Hasta | 22 | 45 |
| Chitra | 20 | 44 |
| Swati | 14 | 38 |
| Vishakha | 14 | 38 |
| Anuradha | 10 | 34 |
| Jyeshtha | 14 | 38 |
| Moola | 20 | 44 |
| Purva Ashadha | 24 | 48 |
| Uttara Ashadha | 20 | 44 |
| Shravana | 10 | 34 |
| Dhanishta | 10 | 34 |
| Shatabhisha | 18 | 42 |
| Purva Bhadrapada | 16 | 40 |
| Uttara Bhadrapada | 24 | 48 |
| Revati | 30 | 54 |

## 3. Event rules

### Vivaha (Marriage)  (`vivaha`)

- **Nakshatras allowed:** Rohini, Mrigashira, Magha, Uttara Phalguni, Hasta, Swati, Anuradha, Moola, Uttara Ashadha, Uttara Bhadrapada, Revati
- **Best nakshatras (bonus):** Rohini, Mrigashira, Uttara Phalguni, Hasta, Uttara Ashadha, Uttara Bhadrapada, Revati
- **Weekdays:** Monday, Wednesday, Thursday, Friday; acceptable with penalty: Sunday
- **Tithis - Shukla good:** 2, 3, 5, 7, 10, 11, 13; acceptable: 1, 12, 15
- **Tithis - Krishna good:** 1, 2, 3, 5; acceptable: 7, 10 (15 = Purnima in Shukla / Amavasya in Krishna)
- **Time of day:** any time of day or night (Marathi: daytime and godhuli only)
- **Lagna:** any (lagna shuddhi still applies); strict lagna shuddhi: yes
- **Moudhyam forbids:** yes; **Adhika masa forbids:** yes; **Dhanurmasa forbids:** yes; **Pitru paksha forbids:** yes
- **Chaturmasa forbids in:** marathi, north
- **Whose stars are checked:** bride, groom
- **Months allowed - telugu:** Chaitra, Vaishakha, Jyeshtha, Shravana, Kartika, Margashira, Magha, Phalguna
- **Months allowed - marathi:** Chaitra, Vaishakha, Jyeshtha, Kartika, Margashira, Pushya, Magha, Phalguna
- **Months allowed - north:** Vaishakha, Jyeshtha, Ashadha, Kartika, Margashira, Magha, Phalguna
- Note: Guru bala for the bride and Surya bala for the groom are scored, not enforced; pandit may prescribe shanti where weak.
- Note: Telugu custom avoids Jyeshtha masa when the bride or groom is the eldest child.

### Nischitartham / Sagai (Engagement)  (`nischitartham`)

- **Nakshatras allowed:** Rohini, Mrigashira, Punarvasu, Pushya, Magha, Uttara Phalguni, Hasta, Chitra, Swati, Anuradha, Moola, Uttara Ashadha, Shravana, Dhanishta, Uttara Bhadrapada, Revati
- **Best nakshatras (bonus):** -
- **Weekdays:** Monday, Wednesday, Thursday, Friday; acceptable with penalty: Sunday
- **Tithis - Shukla good:** 2, 3, 5, 7, 10, 11, 13; acceptable: 1, 6, 12, 15
- **Tithis - Krishna good:** 1, 2, 3, 5; acceptable: 6, 7, 10, 11, 12, 13 (15 = Purnima in Shukla / Amavasya in Krishna)
- **Time of day:** sunrise to sunset
- **Lagna:** Sthira or Dvisvabhava preferred; strict lagna shuddhi: no
- **Moudhyam forbids:** yes; **Adhika masa forbids:** yes; **Dhanurmasa forbids:** no; **Pitru paksha forbids:** yes
- **Chaturmasa forbids in:** north
- **Whose stars are checked:** bride, groom

### Griha Pravesh (House warming)  (`griha_pravesh`)

- **Nakshatras allowed:** Rohini, Mrigashira, Pushya, Uttara Phalguni, Chitra, Anuradha, Uttara Ashadha, Shravana, Dhanishta, Shatabhisha, Uttara Bhadrapada, Revati
- **Best nakshatras (bonus):** Rohini, Mrigashira, Uttara Phalguni, Chitra, Anuradha, Uttara Ashadha, Uttara Bhadrapada, Revati
- **Weekdays:** Monday, Wednesday, Thursday, Friday; acceptable with penalty: Saturday
- **Tithis - Shukla good:** 2, 3, 5, 7, 10, 11, 13; acceptable: 12, 15
- **Tithis - Krishna good:** 2, 3, 5; acceptable: 7, 10, 11 (15 = Purnima in Shukla / Amavasya in Krishna)
- **Time of day:** sunrise to sunset (+ pre-dawn up to 2.5 h before sunrise)
- **Lagna:** Sthira (fixed) preferred; strict lagna shuddhi: no
- **Moudhyam forbids:** yes; **Adhika masa forbids:** yes; **Dhanurmasa forbids:** yes; **Pitru paksha forbids:** yes
- **Chaturmasa forbids in:** marathi, north
- **Whose stars are checked:** kartha
- **Months allowed - telugu:** Vaishakha, Jyeshtha, Shravana, Kartika, Margashira, Magha, Phalguna
- **Months allowed - marathi:** Vaishakha, Jyeshtha, Kartika, Margashira, Magha, Phalguna
- **Months allowed - north:** Vaishakha, Jyeshtha, Kartika, Margashira, Magha, Phalguna
- **Months acceptable (penalty) - telugu:** Shravana, Kartika, Margashira
- **Months acceptable (penalty) - marathi:** Kartika, Margashira
- **Months acceptable (penalty) - north:** Kartika, Margashira
- Note: Sthira lagna is preferred so the family stays settled in the home.

### Bhoomi Puja / Shankusthapana (Foundation)  (`bhoomi_puja`)

- **Nakshatras allowed:** Rohini, Mrigashira, Pushya, Uttara Phalguni, Hasta, Chitra, Swati, Anuradha, Uttara Ashadha, Shravana, Dhanishta, Shatabhisha, Uttara Bhadrapada, Revati
- **Best nakshatras (bonus):** Rohini, Mrigashira, Uttara Phalguni, Chitra, Anuradha, Uttara Ashadha, Uttara Bhadrapada, Revati
- **Weekdays:** Monday, Wednesday, Thursday, Friday; acceptable with penalty: Saturday
- **Tithis - Shukla good:** 2, 3, 5, 7, 10, 11, 13; acceptable: 1, 6, 12, 15
- **Tithis - Krishna good:** 1, 2, 3, 5; acceptable: 6, 7, 10, 11, 12, 13 (15 = Purnima in Shukla / Amavasya in Krishna)
- **Time of day:** sunrise to sunset
- **Lagna:** Sthira (fixed) preferred; strict lagna shuddhi: no
- **Moudhyam forbids:** yes; **Adhika masa forbids:** yes; **Dhanurmasa forbids:** no; **Pitru paksha forbids:** yes
- **Chaturmasa forbids in:** -
- **Whose stars are checked:** kartha
- **Months allowed - telugu:** Vaishakha, Shravana, Kartika, Margashira, Magha, Phalguna
- **Months allowed - marathi:** Vaishakha, Shravana, Kartika, Margashira, Magha, Phalguna
- **Months allowed - north:** Vaishakha, Shravana, Kartika, Margashira, Magha, Phalguna

### Property / Land Purchase or Registration  (`property_purchase`)

- **Nakshatras allowed:** Rohini, Mrigashira, Punarvasu, Pushya, Magha, Uttara Phalguni, Hasta, Vishakha, Anuradha, Moola, Uttara Ashadha, Shravana, Uttara Bhadrapada, Revati
- **Best nakshatras (bonus):** Rohini, Mrigashira, Pushya, Uttara Phalguni, Uttara Ashadha, Uttara Bhadrapada, Revati
- **Weekdays:** Monday, Wednesday, Thursday, Friday; acceptable with penalty: Sunday, Saturday
- **Tithis - Shukla good:** 2, 3, 5, 7, 10, 11, 13; acceptable: 1, 6, 12, 15
- **Tithis - Krishna good:** 1, 2, 3, 5; acceptable: 6, 7, 10, 11, 12, 13 (15 = Purnima in Shukla / Amavasya in Krishna)
- **Time of day:** sunrise to sunset
- **Lagna:** Sthira (fixed) preferred; strict lagna shuddhi: no
- **Moudhyam forbids:** no; **Adhika masa forbids:** no; **Dhanurmasa forbids:** no; **Pitru paksha forbids:** yes
- **Chaturmasa forbids in:** -
- **Whose stars are checked:** kartha
- Swayam-siddha days override the nakshatra/tithi list.

### Vahana (Vehicle purchase / delivery)  (`vehicle_purchase`)

- **Nakshatras allowed:** Ashwini, Rohini, Mrigashira, Punarvasu, Pushya, Uttara Phalguni, Hasta, Chitra, Swati, Anuradha, Uttara Ashadha, Shravana, Dhanishta, Shatabhisha, Uttara Bhadrapada, Revati
- **Best nakshatras (bonus):** Ashwini, Punarvasu, Pushya, Hasta, Swati, Shravana, Dhanishta, Shatabhisha, Revati
- **Weekdays:** Monday, Wednesday, Thursday, Friday; acceptable with penalty: Sunday
- **Tithis - Shukla good:** 2, 3, 5, 7, 10, 11, 13; acceptable: 1, 6, 12, 15
- **Tithis - Krishna good:** 1, 2, 3, 5; acceptable: 6, 7, 10, 11, 12, 13 (15 = Purnima in Shukla / Amavasya in Krishna)
- **Time of day:** sunrise to sunset
- **Lagna:** Chara (movable) preferred; strict lagna shuddhi: no
- **Moudhyam forbids:** no; **Adhika masa forbids:** no; **Dhanurmasa forbids:** no; **Pitru paksha forbids:** yes
- **Chaturmasa forbids in:** -
- **Whose stars are checked:** kartha
- Swayam-siddha days override the nakshatra/tithi list.

### Vyapara Arambha (Business / shop / office opening)  (`vyapara`)

- **Nakshatras allowed:** Ashwini, Rohini, Mrigashira, Pushya, Uttara Phalguni, Hasta, Chitra, Anuradha, Uttara Ashadha, Shravana, Dhanishta, Uttara Bhadrapada, Revati
- **Best nakshatras (bonus):** Ashwini, Rohini, Pushya, Uttara Phalguni, Hasta, Uttara Ashadha, Uttara Bhadrapada, Revati
- **Weekdays:** Monday, Wednesday, Thursday, Friday; acceptable with penalty: Sunday
- **Tithis - Shukla good:** 2, 3, 5, 7, 10, 11, 13; acceptable: 1, 6, 12, 15
- **Tithis - Krishna good:** 1, 2, 3, 5; acceptable: 6, 7, 10, 11, 12, 13 (15 = Purnima in Shukla / Amavasya in Krishna)
- **Time of day:** sunrise to sunset
- **Lagna:** Sthira (fixed) preferred; strict lagna shuddhi: no
- **Moudhyam forbids:** no; **Adhika masa forbids:** yes; **Dhanurmasa forbids:** no; **Pitru paksha forbids:** yes
- **Chaturmasa forbids in:** -
- **Whose stars are checked:** kartha
- Swayam-siddha days override the nakshatra/tithi list.

### Joining a new job / starting a new role  (`job_joining`)

- **Nakshatras allowed:** Ashwini, Rohini, Mrigashira, Punarvasu, Pushya, Uttara Phalguni, Hasta, Chitra, Swati, Anuradha, Uttara Ashadha, Shravana, Dhanishta, Uttara Bhadrapada, Revati
- **Best nakshatras (bonus):** -
- **Weekdays:** Sunday, Monday, Wednesday, Thursday, Friday
- **Tithis - Shukla good:** 2, 3, 5, 7, 10, 11, 13; acceptable: 1, 6, 12, 15
- **Tithis - Krishna good:** 1, 2, 3, 5; acceptable: 6, 7, 10, 11, 12, 13 (15 = Purnima in Shukla / Amavasya in Krishna)
- **Time of day:** sunrise to sunset
- **Lagna:** Sthira or Dvisvabhava preferred; strict lagna shuddhi: no
- **Moudhyam forbids:** no; **Adhika masa forbids:** no; **Dhanurmasa forbids:** no; **Pitru paksha forbids:** no
- **Chaturmasa forbids in:** -
- **Whose stars are checked:** kartha

### Gold / Jewellery purchase  (`jewellery_purchase`)

- **Nakshatras allowed:** Ashwini, Rohini, Punarvasu, Pushya, Uttara Phalguni, Hasta, Chitra, Swati, Anuradha, Uttara Ashadha, Shravana, Dhanishta, Uttara Bhadrapada, Revati
- **Best nakshatras (bonus):** Ashwini, Rohini, Pushya, Revati
- **Weekdays:** Sunday, Monday, Wednesday, Thursday, Friday
- **Tithis - Shukla good:** 2, 3, 5, 7, 10, 11, 13; acceptable: 1, 6, 12, 15
- **Tithis - Krishna good:** 1, 2, 3, 5; acceptable: 6, 7, 10, 11, 12, 13 (15 = Purnima in Shukla / Amavasya in Krishna)
- **Time of day:** sunrise to sunset
- **Lagna:** Sthira (fixed) preferred; strict lagna shuddhi: no
- **Moudhyam forbids:** no; **Adhika masa forbids:** no; **Dhanurmasa forbids:** no; **Pitru paksha forbids:** yes
- **Chaturmasa forbids in:** -
- **Whose stars are checked:** kartha
- Swayam-siddha days override the nakshatra/tithi list.

### Yatra (Travel / pilgrimage start)  (`yatra`)

- **Nakshatras allowed:** Ashwini, Mrigashira, Punarvasu, Pushya, Hasta, Anuradha, Shravana, Dhanishta, Revati
- **Best nakshatras (bonus):** -
- **Weekdays:** Sunday, Monday, Tuesday, Wednesday, Thursday, Friday, Saturday
- **Tithis - Shukla good:** 2, 3, 5, 7, 10, 11, 13; acceptable: 1, 6, 12, 15
- **Tithis - Krishna good:** 1, 2, 3, 5; acceptable: 6, 7, 10, 11, 12, 13 (15 = Purnima in Shukla / Amavasya in Krishna)
- **Time of day:** sunrise to sunset
- **Lagna:** Chara (movable) preferred; strict lagna shuddhi: no
- **Moudhyam forbids:** no; **Adhika masa forbids:** no; **Dhanurmasa forbids:** no; **Pitru paksha forbids:** no
- **Chaturmasa forbids in:** -
- **Whose stars are checked:** kartha
- Note: Disha-shoola (weekday vs direction) is enforced.

### Namakarana (Naming ceremony)  (`namakarana`)

- **Nakshatras allowed:** Ashwini, Rohini, Mrigashira, Punarvasu, Pushya, Uttara Phalguni, Hasta, Chitra, Swati, Anuradha, Uttara Ashadha, Shravana, Dhanishta, Shatabhisha, Uttara Bhadrapada, Revati
- **Best nakshatras (bonus):** -
- **Weekdays:** Monday, Wednesday, Thursday, Friday; acceptable with penalty: Sunday
- **Tithis - Shukla good:** 2, 3, 5, 7, 10, 11, 13; acceptable: 1, 6, 12, 15
- **Tithis - Krishna good:** 1, 2, 3, 5; acceptable: 6, 7, 10, 11, 12, 13 (15 = Purnima in Shukla / Amavasya in Krishna)
- **Time of day:** sunrise to sunset
- **Lagna:** Sthira or Dvisvabhava preferred; strict lagna shuddhi: no
- **Moudhyam forbids:** no; **Adhika masa forbids:** no; **Dhanurmasa forbids:** no; **Pitru paksha forbids:** no
- **Chaturmasa forbids in:** -
- **Whose stars are checked:** child
- Note: Traditionally on the 11th, 12th or 16th day after birth, or any good day later.

### Annaprashana (First rice feeding)  (`annaprashana`)

- **Nakshatras allowed:** Ashwini, Rohini, Mrigashira, Punarvasu, Pushya, Uttara Phalguni, Hasta, Chitra, Swati, Anuradha, Uttara Ashadha, Shravana, Dhanishta, Shatabhisha, Uttara Bhadrapada, Revati
- **Best nakshatras (bonus):** -
- **Weekdays:** Monday, Wednesday, Thursday, Friday
- **Tithis - Shukla good:** 2, 3, 5, 7, 10, 11, 13; acceptable: 1, 6, 12, 15
- **Tithis - Krishna good:** 1, 2, 3, 5; acceptable: 6, 7, 10, 11, 12, 13 (15 = Purnima in Shukla / Amavasya in Krishna)
- **Time of day:** sunrise to about 1:30 pm
- **Lagna:** Sthira or Dvisvabhava preferred; strict lagna shuddhi: no
- **Moudhyam forbids:** no; **Adhika masa forbids:** yes; **Dhanurmasa forbids:** no; **Pitru paksha forbids:** yes
- **Chaturmasa forbids in:** -
- **Whose stars are checked:** child
- Note: Boys in even months (6th, 8th), girls in odd months (5th, 7th) of age - engine checks this.

### Chudakarana / Mundan (First haircut)  (`chudakarana`)

- **Nakshatras allowed:** Ashwini, Mrigashira, Punarvasu, Pushya, Hasta, Chitra, Swati, Jyeshtha, Shravana, Dhanishta, Shatabhisha, Revati
- **Best nakshatras (bonus):** -
- **Weekdays:** Monday, Wednesday, Thursday, Friday
- **Tithis - Shukla good:** 2, 3, 5, 7, 10, 11, 13; acceptable: 1, 6, 12, 15
- **Tithis - Krishna good:** 1, 2, 3, 5; acceptable: 6, 7, 10, 11, 12, 13 (15 = Purnima in Shukla / Amavasya in Krishna)
- **Time of day:** sunrise to about 1:30 pm
- **Lagna:** any (lagna shuddhi still applies); strict lagna shuddhi: no
- **Moudhyam forbids:** no; **Adhika masa forbids:** yes; **Dhanurmasa forbids:** no; **Pitru paksha forbids:** yes
- **Chaturmasa forbids in:** north
- **Whose stars are checked:** child
- Note: Usually in the 1st, 3rd or 5th year (odd years).

### Karnavedha (Ear piercing)  (`karnavedha`)

- **Nakshatras allowed:** Ashwini, Mrigashira, Punarvasu, Pushya, Hasta, Chitra, Anuradha, Shravana, Dhanishta, Revati
- **Best nakshatras (bonus):** -
- **Weekdays:** Monday, Wednesday, Thursday, Friday
- **Tithis - Shukla good:** 2, 3, 5, 7, 10, 11, 13; acceptable: 1, 6, 12, 15
- **Tithis - Krishna good:** 1, 2, 3, 5; acceptable: 6, 7, 10, 11, 12, 13 (15 = Purnima in Shukla / Amavasya in Krishna)
- **Time of day:** sunrise to about 1:30 pm
- **Lagna:** any (lagna shuddhi still applies); strict lagna shuddhi: no
- **Moudhyam forbids:** no; **Adhika masa forbids:** yes; **Dhanurmasa forbids:** no; **Pitru paksha forbids:** yes
- **Chaturmasa forbids in:** -
- **Whose stars are checked:** child

### Aksharabhyasam / Vidyarambha (Start of learning)  (`aksharabhyasam`)

- **Nakshatras allowed:** Ashwini, Mrigashira, Ardra, Punarvasu, Pushya, Purva Phalguni, Hasta, Chitra, Swati, Anuradha, Moola, Purva Ashadha, Shravana, Dhanishta, Shatabhisha, Purva Bhadrapada, Revati
- **Best nakshatras (bonus):** Ashwini, Punarvasu, Pushya, Hasta, Shravana, Revati
- **Weekdays:** Sunday, Wednesday, Thursday, Friday; acceptable with penalty: Monday
- **Tithis - Shukla good:** 2, 3, 5, 6, 10, 11, 12; acceptable: 7, 13, 15
- **Tithis - Krishna good:** 1, 2, 3, 5; acceptable: 6, 7, 10, 11, 12, 13 (15 = Purnima in Shukla / Amavasya in Krishna)
- **Time of day:** sunrise to about 1:30 pm
- **Lagna:** Dvisvabhava (dual) preferred; strict lagna shuddhi: no
- **Moudhyam forbids:** yes; **Adhika masa forbids:** yes; **Dhanurmasa forbids:** no; **Pitru paksha forbids:** yes
- **Chaturmasa forbids in:** -
- **Whose stars are checked:** child
- Swayam-siddha days override the nakshatra/tithi list.
- Note: Vasant Panchami and Vijayadashami are especially auspicious.

### Upanayana (Sacred thread ceremony)  (`upanayana`)

- **Nakshatras allowed:** Ashwini, Rohini, Mrigashira, Punarvasu, Pushya, Purva Phalguni, Uttara Phalguni, Hasta, Chitra, Swati, Anuradha, Purva Ashadha, Uttara Ashadha, Shravana, Dhanishta, Shatabhisha, Purva Bhadrapada, Uttara Bhadrapada, Revati
- **Best nakshatras (bonus):** -
- **Weekdays:** Sunday, Monday, Wednesday, Thursday, Friday
- **Tithis - Shukla good:** 2, 3, 5, 10, 11, 12; acceptable: 7, 13
- **Tithis - Krishna good:** 2, 3, 5; acceptable: - (15 = Purnima in Shukla / Amavasya in Krishna)
- **Time of day:** sunrise to about 1:30 pm
- **Lagna:** any (lagna shuddhi still applies); strict lagna shuddhi: yes
- **Moudhyam forbids:** yes; **Adhika masa forbids:** yes; **Dhanurmasa forbids:** yes; **Pitru paksha forbids:** yes
- **Chaturmasa forbids in:** -
- **Whose stars are checked:** child
- **Months allowed - telugu:** Chaitra, Vaishakha, Jyeshtha, Magha, Phalguna
- **Months allowed - marathi:** Chaitra, Vaishakha, Jyeshtha, Magha, Phalguna
- **Months allowed - north:** Chaitra, Vaishakha, Jyeshtha, Magha, Phalguna
- Note: Uttarayana and Shukla paksha are strongly preferred.

### Seemantham / Godh Bharai (Baby shower)  (`seemantham`)

- **Nakshatras allowed:** Rohini, Mrigashira, Punarvasu, Pushya, Uttara Phalguni, Hasta, Anuradha, Moola, Uttara Ashadha, Shravana, Uttara Bhadrapada, Revati
- **Best nakshatras (bonus):** -
- **Weekdays:** Sunday, Tuesday, Thursday; acceptable with penalty: Monday, Wednesday, Friday
- **Tithis - Shukla good:** 2, 3, 5, 7, 10, 11, 13; acceptable: 1, 6, 12, 15
- **Tithis - Krishna good:** 1, 2, 3, 5; acceptable: 6, 7, 10, 11, 12, 13 (15 = Purnima in Shukla / Amavasya in Krishna)
- **Time of day:** sunrise to about 1:30 pm
- **Lagna:** any (lagna shuddhi still applies); strict lagna shuddhi: no
- **Moudhyam forbids:** no; **Adhika masa forbids:** yes; **Dhanurmasa forbids:** no; **Pitru paksha forbids:** yes
- **Chaturmasa forbids in:** -
- **Whose stars are checked:** wife
- Note: Usually done in the 5th, 7th or 9th month of pregnancy (family custom varies).

### Pooja / Homa / Vratam (Satyanarayana, Ganapati homa, etc.)  (`pooja`)

- **Nakshatras allowed:** all
- **Best nakshatras (bonus):** Ashwini, Rohini, Mrigashira, Pushya, Uttara Phalguni, Hasta, Chitra, Anuradha, Uttara Ashadha, Uttara Bhadrapada, Revati
- **Weekdays:** Sunday, Monday, Tuesday, Wednesday, Thursday, Friday, Saturday
- **Tithis - Shukla good:** 2, 3, 5, 7, 10, 11, 13, 15; acceptable: 1, 4, 6, 8, 9, 12, 14
- **Tithis - Krishna good:** 1, 2, 3, 5, 11; acceptable: 4, 6, 7, 8, 9, 10, 12, 13, 14, 15 (15 = Purnima in Shukla / Amavasya in Krishna)
- **Time of day:** sunrise to sunset
- **Lagna:** any (lagna shuddhi still applies); strict lagna shuddhi: no
- **Moudhyam forbids:** no; **Adhika masa forbids:** no; **Dhanurmasa forbids:** no; **Pitru paksha forbids:** no
- **Chaturmasa forbids in:** -
- **Whose stars are checked:** kartha
- Note: Satyanarayana vratam is best on Purnima, Ekadashi or Sankranti; Shiva poojas suit Pradosha and Masa-shivaratri - the Acharya should mention these.

### Devata Pratishtha (Idol installation)  (`pratishtha`)

- **Nakshatras allowed:** Ashwini, Rohini, Mrigashira, Punarvasu, Pushya, Uttara Phalguni, Hasta, Chitra, Swati, Anuradha, Uttara Ashadha, Shravana, Dhanishta, Shatabhisha, Uttara Bhadrapada, Revati
- **Best nakshatras (bonus):** Rohini, Mrigashira, Pushya, Uttara Phalguni, Chitra, Anuradha, Uttara Ashadha, Shravana, Uttara Bhadrapada, Revati
- **Weekdays:** Monday, Wednesday, Thursday, Friday
- **Tithis - Shukla good:** 2, 3, 5, 7, 10, 11, 13; acceptable: 1, 6, 12, 15
- **Tithis - Krishna good:** 1, 2, 3, 5; acceptable: 6, 7, 10, 11, 12, 13 (15 = Purnima in Shukla / Amavasya in Krishna)
- **Time of day:** sunrise to sunset
- **Lagna:** Sthira (fixed) preferred; strict lagna shuddhi: yes
- **Moudhyam forbids:** yes; **Adhika masa forbids:** yes; **Dhanurmasa forbids:** yes; **Pitru paksha forbids:** yes
- **Chaturmasa forbids in:** -
- **Whose stars are checked:** kartha
- **Months allowed - telugu:** Chaitra, Vaishakha, Jyeshtha, Magha, Phalguna
- **Months allowed - marathi:** Chaitra, Vaishakha, Jyeshtha, Magha, Phalguna
- **Months allowed - north:** Chaitra, Vaishakha, Jyeshtha, Magha, Phalguna

### General auspicious beginning  (`general`)

- **Nakshatras allowed:** Ashwini, Rohini, Mrigashira, Punarvasu, Pushya, Uttara Phalguni, Hasta, Chitra, Swati, Anuradha, Uttara Ashadha, Shravana, Dhanishta, Shatabhisha, Uttara Bhadrapada, Revati
- **Best nakshatras (bonus):** -
- **Weekdays:** Monday, Wednesday, Thursday, Friday; acceptable with penalty: Sunday
- **Tithis - Shukla good:** 2, 3, 5, 7, 10, 11, 13; acceptable: 1, 6, 12, 15
- **Tithis - Krishna good:** 1, 2, 3, 5; acceptable: 6, 7, 10, 11, 12, 13 (15 = Purnima in Shukla / Amavasya in Krishna)
- **Time of day:** sunrise to sunset
- **Lagna:** Sthira or Dvisvabhava preferred; strict lagna shuddhi: no
- **Moudhyam forbids:** no; **Adhika masa forbids:** yes; **Dhanurmasa forbids:** no; **Pitru paksha forbids:** yes
- **Chaturmasa forbids in:** -
- **Whose stars are checked:** kartha

## 4. Scoring and quality labels

Start 50. Bonuses for best nakshatra (+8), good tithi (+6), good weekday (+5), favourable tara/chandra (+3 each per person),
preferred lagna (+5 to +8), benefics in kendra (+2/+3), Abhijit (+4), Amrita (+5), Sarvartha Siddhi (+6), swayam-siddha (+8),
comfortable window length (up to +4). Penalties for acceptable-but-not-ideal factors. Capped at 100.

| Score | Label shown |
|---|---|
| 85+ | Uttama (excellent) |
| 72-84 | Shubha (good) |
| 60-71 | Madhyama (acceptable) |
| below 60 | Adhama - only shown if nothing better exists |
