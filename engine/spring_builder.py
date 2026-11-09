import os
import json
import re
import time
import math
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timezone

# ==========================================
# ENVIRONMENT CONFIGURATION
# ==========================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
SITE_BASE_URL = os.environ.get("SITE_BASE_URL", "https://hanifsalman11.github.io/torsion-spring-index").rstrip("/")
INDEXNOW_KEY = os.environ.get("INDEXNOW_KEY", "d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6").strip()
CUSTOM_SPRING = os.environ.get("CUSTOM_SPRING", "").strip()
PAGES_PER_RUN = int(os.environ.get("PAGES_PER_RUN", "3"))

DOCS_DIR = "docs"
DATA_DIR = "data"
PUBLISHED_FILE = os.path.join(DATA_DIR, "published_springs.json")
MONETIZATION_FILE = os.path.join(DATA_DIR, "monetization.json")

_CACHED_MODELS = None

# Format: (Spring Spec / Door Scenario, Wire Dia In, Inside Dia In, Length In, Door Height Ft, Pair Balanced Door Lbs, Color Code)
SEED_SPRINGS = [
    ("0.192 × 2\" × 20\" Torsion Spring Pair (16x7 Light Door)", 0.192, 2.00, 20.0, 7, 138, "Blue Painted Tip"),
    ("0.207 × 1.75\" × 23\" Torsion Spring Pair (Standard 16x7)", 0.207, 1.75, 23.0, 7, 168, "Yellow Painted Tip"),
    ("0.207 × 2\" × 22\" Torsion Spring Pair (16x7 Non-Insulated)", 0.207, 2.00, 22.0, 7, 165, "Yellow Painted Tip"),
    ("0.207 × 2\" × 24\" Torsion Spring Pair (High-Cycle 16x7)", 0.207, 2.00, 24.0, 7, 152, "Yellow Painted Tip"),
    ("0.218 × 2\" × 23\" Torsion Spring Pair (16x7 Insulated)", 0.218, 2.00, 23.0, 7, 192, "Red Painted Tip"),
    ("0.218 × 2\" × 24\" Torsion Spring Pair (16x7 Vinyl-Backed)", 0.218, 2.00, 24.0, 7, 184, "Red Painted Tip"),
    ("0.218 × 2\" × 26\" Torsion Spring Pair (High-Cycle 16x7)", 0.218, 2.00, 26.0, 7, 170, "Red Painted Tip"),
    ("0.225 × 2\" × 24\" Torsion Spring Pair (16x7 Steel-Backed)", 0.225, 2.00, 24.0, 7, 212, "Brown / Purple Tip"),
    ("0.225 × 2\" × 25\" Torsion Spring Pair (16x7 Double-Steel)", 0.225, 2.00, 25.0, 7, 204, "Brown / Purple Tip"),
    ("0.225 × 2\" × 26\" Torsion Spring Pair (16x7 Heavy Door)", 0.225, 2.00, 26.0, 7, 196, "Brown / Purple Tip"),
    ("0.225 × 2\" × 28\" Torsion Spring Pair (High-Cycle 16x7)", 0.225, 2.00, 28.0, 7, 182, "Brown / Purple Tip"),
    ("0.234 × 2\" × 25\" Torsion Spring Pair (16x7 Carriage Door)", 0.234, 2.00, 25.0, 7, 240, "Orange / Green Tip"),
    ("0.234 × 2\" × 27\" Torsion Spring Pair (16x7 Polyurethane)", 0.234, 2.00, 27.0, 7, 222, "Orange / Green Tip"),
    ("0.234 × 2\" × 29\" Torsion Spring Pair (16x8 Insulated Door)", 0.234, 2.00, 29.0, 8, 234, "Orange / Green Tip"),
    ("0.243 × 2\" × 26\" Torsion Spring Pair (16x7 Wood/Glass)", 0.243, 2.00, 26.0, 7, 272, "Gold Painted Tip"),
    ("0.243 × 2\" × 28\" Torsion Spring Pair (16x8 Double-Steel)", 0.243, 2.00, 28.0, 8, 286, "Gold Painted Tip"),
    ("0.243 × 2\" × 30\" Torsion Spring Pair (High-Cycle 16x8)", 0.243, 2.00, 30.0, 8, 266, "Gold Painted Tip"),
    ("0.250 × 2\" × 28\" Torsion Spring Pair (16x7 Heavy Wood)", 0.250, 2.00, 28.0, 7, 290, "White / Blue Tip"),
    ("0.250 × 2\" × 30\" Torsion Spring Pair (16x8 Carriage House)", 0.250, 2.00, 30.0, 8, 308, "White / Blue Tip"),
    ("0.250 × 2\" × 32\" Torsion Spring Pair (18x8 Insulated Door)", 0.250, 2.00, 32.0, 8, 288, "White / Blue Tip"),
    ("0.262 × 2\" × 32\" Torsion Spring Pair (16x8 Full-View Glass)", 0.262, 2.00, 32.0, 8, 355, "Green Painted Tip"),
    ("0.273 × 2\" × 34\" Torsion Spring Pair (Commercial / Custom)", 0.273, 2.00, 34.0, 8, 405, "Tan Painted Tip"),
    ("8x7 Single-Car Garage Door (95 Lbs) Torsion Spring Sizing", 0.207, 2.00, 24.0, 7, 95, "Single / Dual Conversion"),
    ("9x7 Insulated Single Garage Door (125 Lbs) Spring Sizing", 0.225, 2.00, 25.0, 7, 125, "Single / Dual Conversion"),
    ("16x7 Non-Insulated 2-Car Pan Door (155 Lbs) Spring Sizing", 0.207, 2.00, 23.0, 7, 155, "Yellow Painted Tip"),
    ("16x7 Polystyrene Insulated 2-Car Door (195 Lbs) Sizing", 0.218, 2.00, 23.0, 7, 195, "Red Painted Tip"),
    ("16x7 Triple-Layer Polyurethane Door (235 Lbs) Sizing", 0.234, 2.00, 25.0, 7, 235, "Orange Painted Tip"),
    ("16x8 Tall 2-Car Insulated Garage Door (255 Lbs) Sizing", 0.243, 2.00, 29.0, 8, 255, "Gold Painted Tip"),
    ("Wayne Dalton TorqueMaster to Standard Torsion Conversion", 0.218, 2.00, 24.0, 7, 185, "Standard 1\" Tube Kit"),
    ("Single Torsion Spring to Dual 2-Spring Conversion Sizing", 0.207, 2.00, 24.0, 7, 155, "2x Cycle Life Upgrade")
]


def load_json(filepath, default):
    """Self-healing JSON loader: otomatis pulih jika file korup atau kosong."""
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, type(default)) else default
        except Exception as e:
            print(f"[SELF-HEAL] Recovering {filepath} due to read notice: {e}")
    return default


def save_json(filepath, data):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    return re.sub(r"[\s-]+", "-", text).strip("-")


def safe_float(val, default=0.218):
    try:
        cleaned = re.sub(r"[^0-9.]", "", str(val))
        return float(cleaned) if cleaned else float(default)
    except Exception:
        return float(default)


def build_amazon_url(search_keywords, mon_cfg):
    domain = mon_cfg.get("marketplace_domain", "www.amazon.com")
    tag = mon_cfg.get("amazon_associate_tag", "YOUR_AMAZON_TAG-20")
    encoded_q = urllib.parse.quote_plus(search_keywords)
    return f"https://{domain}/s?k={encoded_q}&tag={tag}"


def get_active_gemini_model(api_key):
    """
    LAPIS 1: Mesin Pemindai Versi Otomatis berbasis Regex tanpa angka versi manual.
    Otomatis mendeteksi model Gemini Flash STABIL generasi tertinggi lintas tahun.
    """
    global _CACHED_MODELS
    if _CACHED_MODELS is not None:
        return _CACHED_MODELS

    list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        req = urllib.request.Request(list_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            scored_models = []

            for m in data.get("models", []):
                name = m.get("name", "").replace("models/", "")
                methods = m.get("supportedGenerationMethods", [])

                if "generateContent" not in methods or "flash" not in name.lower():
                    continue

                if any(bad in name.lower() for bad in [
                    "preview", "exp", "thinking", "image", "tts", "audio", "vision", "8b"
                ]):
                    continue

                ver_match = re.search(r"gemini-(\d+(?:\.\d+)?)-flash", name.lower())
                if ver_match:
                    ver_num = float(ver_match.group(1))
                    if name.lower() == f"gemini-{ver_match.group(1)}-flash":
                        tier_score = 2
                    elif name.lower() == f"gemini-{ver_match.group(1)}-flash-lite":
                        tier_score = 1
                    else:
                        tier_score = 0
                    scored_models.append((ver_num, tier_score, name))
                elif name.lower() == "gemini-flash-latest":
                    scored_models.append((0.1, 0, name))

            if scored_models:
                scored_models.sort(key=lambda x: (x[0], x[1]), reverse=True)
                _CACHED_MODELS = [item[2] for item in scored_models[:2]]
                print(f"[GEMINI] Future-proof active models locked: {_CACHED_MODELS}")
                return _CACHED_MODELS
    except Exception as e:
        print(f"[WARN] Dynamic model discovery notice: {e}")

    _CACHED_MODELS = ["gemini-flash-latest"]
    return _CACHED_MODELS


def discover_google_spring_queries(published_slugs):
    """
    LAPIS 4: 3-Tier Infinite Keyword Supply:
    Tier A: Seed List -> Tier B: Google Suggest US -> Tier C: Combinatorial Wire × ID × Length Permutator.
    """
    discovered = []
    seeds = [
        "garage door torsion spring calculator ",
        "what size torsion spring for ",
        "207 x 2 x ",
        "225 x 2 x ",
        "218 x 2 x "
    ]
    for seed in seeds:
        try:
            url = f"http://suggestqueries.google.com/complete/search?client=firefox&hl=en&gl=us&q={urllib.parse.quote(seed)}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for suggestion in data[1]:
                    cleaned = suggestion.lower()
                    for pref in seeds:
                        if "calculator" in pref or "what size" in pref:
                            cleaned = cleaned.replace(pref, "")
                    cleaned = re.sub(
                        r"\b(calculator|size|sizing|chart|manual|review|reddit|for)\b",
                        "",
                        cleaned
                    ).strip()
                    if 5 <= len(cleaned) <= 42:
                        w_m = re.search(r"(192|207|218|225|234|243|250|262)", cleaned)
                        wire_d = float("0." + w_m.group(1)) if w_m else 0.218
                        discovered.append((cleaned.title(), wire_d, 2.00, 24.0, 7, 190, "DASMA Standard"))
        except Exception as e:
            print(f"[WARN] Google Suggest notice: {e}")

    # Tier C Fallback: Combinatorial Permutator (Anti-Habis Lintas Tahun)
    wires = [
        (0.192, "Blue Tip"),
        (0.207, "Yellow Tip"),
        (0.218, "Red Tip"),
        (0.225, "Brown Tip"),
        (0.234, "Orange Tip"),
        (0.243, "Gold Tip"),
        (0.250, "White Tip")
    ]
    inside_dias = [1.75, 2.00]
    lengths = [21.0, 22.0, 23.0, 24.0, 25.0, 26.0, 27.0, 28.0, 29.0, 30.0, 31.0, 32.0]
    for w_dia, c_code in wires:
        for id_in in inside_dias:
            for l_in in lengths:
                combo_title = f"{w_dia:.3f} × {id_in:g}\" × {int(l_in)}\" Torsion Spring Pair"
                test_slug = slugify(f"{combo_title}-ippt-turns-calculator")
                if test_slug not in published_slugs:
                    active_coils = l_in / w_dia
                    mean_d = id_in + w_dia
                    ippt_1 = (30000000.0 * (w_dia ** 4)) / (3670.0 * mean_d * active_coils)
                    d_ht = 8 if l_in >= 29.0 else 7
                    turns = 8.5 if d_ht == 8 else 7.5
                    door_wt = int(round((2.0 * ippt_1 * turns) / 2.0))
                    discovered.append((combo_title, w_dia, id_in, l_in, d_ht, door_wt, c_code))
                    if len(discovered) >= 25:
                        return discovered
    return discovered


def build_deterministic_spring_data(spr_tuple):
    """
    LAPIS 3: Mesin Fisika Mekanika Pegas Torsi DASMA, 20-Coil Micrometer & IPPT (100% Bebas Gagal).
    """
    item_name, wire_in, id_in, len_in, door_ht_ft, ref_door_lbs, color_code = spr_tuple

    # 1. Pengukuran 20 Lilitan (20-Coil Length) & 10-Coil Length dalam Inci:
    twenty_coil_in = round(wire_in * 20.0, 2)
    ten_coil_in = round(wire_in * 10.0, 2)

    # 2. Jumlah Lilitan Aktif (Active Coils = Body Length / Wire Dia):
    active_coils = int(round(len_in / wire_in))
    mean_dia_in = round(id_in + wire_in, 3)

    # 3. Rumus Mekanika IPPT (Inch-Pounds Per Turn) per 1 Pegas:
    # IPPT = (E * d^4) / (3670 * Mean_Diameter * Active_Coils), E = 30 x 10^6 PSI (ASTM A229 Oil-Tempered Wire)
    ippt_single = round((30000000.0 * (wire_in ** 4)) / (3670.0 * mean_dia_in * active_coils), 2)
    ippt_pair = round(ippt_single * 2.0, 2)

    # 4. Jumlah Putaran Winding Bar (Turns) pada Drum Standar 4" (OSE 400-8 / 400-96, Radius = 2.0"):
    winding_turns = 8.5 if door_ht_ft >= 8 else 7.5
    quarter_turns = int(round(winding_turns * 4.0))

    # 5. Berat Pintu Garasi yang Diseimbangkan (Balanced Door Weight Lbs = Total Torque / Drum Radius 2.0"):
    balanced_pair_lbs = int(round((ippt_pair * winding_turns) / 2.0))
    balanced_single_lbs = int(round(balanced_pair_lbs / 2.0))

    # 6. Rekomendasi High-Cycle Upgrade (+1 ukuran kawat lebih tebal & ~28% lebih panjang untuk 25,000+ siklus):
    hc_wire = round(wire_in + 0.012, 3)
    hc_len = int(round(len_in * 1.26))

    return {
        "spring_name": item_name,
        "color_code": color_code,
        "seo_title": f"{item_name} IPPT, Door Weight & Winding Turns Calculator (2026)",
        "meta_description": f"Calculate exact IPPT torque ({ippt_single} IPPT/spring), balanced door weight ({balanced_pair_lbs} lbs pair / {balanced_single_lbs} lbs single), 20-coil wire size ({twenty_coil_in}\"), and {quarter_turns} quarter-turns for {item_name}.",
        "specs": {
            "wire_diameter_in": wire_in,
            "inside_diameter_in": id_in,
            "spring_length_in": len_in,
            "twenty_coil_length_in": twenty_coil_in,
            "ten_coil_length_in": ten_coil_in,
            "active_coils": active_coils,
            "ippt_per_spring": ippt_single,
            "ippt_pair_total": ippt_pair,
            "door_height_ft": door_ht_ft,
            "winding_full_turns": winding_turns,
            "winding_quarter_turns": quarter_turns,
            "balanced_door_lbs_pair": balanced_pair_lbs,
            "balanced_door_lbs_single": balanced_single_lbs,
            "high_cycle_upgrade_spec": f"{hc_wire:.3f}\" × {id_in:g}\" × {hc_len}\" (25,000+ Cycles)",
            "color_code": color_code
        },
        "dasma_verdict": f"Constructed from {wire_in:.3f}-inch ASTM A229 oil-tempered carbon steel wire ({twenty_coil_in}\" across 20 coils, {color_code}) with a {id_in:g}-inch inside diameter and {len_in:g}-inch body length ({active_coils} active coils), each {item_name} generates {ippt_single} IPPT (Inch-Pounds Per Turn) of torque. Wound to {winding_turns} full turns ({quarter_turns} quarter-turns with winding bars) on standard 4-inch drums for a {door_ht_ft}-foot tall door, a matched pair counterbalances a {balanced_pair_lbs}-lb garage door ({balanced_single_lbs} lbs for a single-spring setup). For a 25,000-cycle extended-life upgrade at the exact same IPPT, step up to {hc_wire:.3f}\" × {id_in:g}\" × {hc_len}\" springs.",
        "hardware_bundle": [
            {
                "badge": f"{wire_in:.3f} × {id_in:g}\" × {len_in:g}\" Pair",
                "title": f"Matched Pair ({wire_in:.3f}\" × {id_in:g}\" × {len_in:g}\") Electrophoresis Black Torsion Springs + Steel Winding Bars",
                "price_range": "$74 - $169",
                "amazon_query": f"{wire_in:.3f} x {id_in:g} x {int(len_in)} Garage Door Torsion Springs Pair Winding Bars",
                "spr_note": f"Includes Left-Wound and Right-Wound cones pre-installed plus two 1/2\" × 18\" knurled cold-rolled steel winding bars."
            },
            {
                "badge": "400-8 Drums & 1/8\" Cables",
                "title": f"Pair of 400-{door_ht_ft} Cast Aluminum Torsion Cable Drums + 1/8\" 7×19 Galvanized Lift Cables & Center Bearing",
                "price_range": "$42 - $89",
                "amazon_query": "Garage Door 400-8 Cable Drums 1/8 Lift Cables Center Bearing Kit",
                "spr_note": "Always replace frayed bottom lift cables and worn center nylon bushings while the torsion tube is unweighted."
            },
            {
                "badge": "Quiet 11-Ball Nylon Rollers",
                "title": "Sealed 6200ZZ 11-Ball Bearing Quiet Nylon Garage Door Rollers (12-Pack) + 3-IN-ONE Garage Lube",
                "price_range": "$34 - $69",
                "amazon_query": "Quiet Nylon Garage Door Rollers 6200ZZ 11 Ball Bearing 12 Pack",
                "spr_note": "Cuts garage door rolling noise by 75% and reduces drag on your torsion springs and opener motor."
            },
            {
                "badge": "Jackshaft / Belt Opener",
                "title": "Wall-Mount Jackshaft or Ultra-Quiet Belt-Drive Wi-Fi Garage Door Opener w/ Battery Backup",
                "price_range": "$229 - $579",
                "amazon_query": "Chamberlain LiftMaster Wall Mount Jackshaft Belt Drive Garage Door Opener",
                "spr_note": f"Once your {balanced_pair_lbs}-lb door is properly balanced by new torsion springs, the opener lifts it with <10 lbs of effort."
            }
        ],
        "safety_checklist": [
            f"Measure 20 Coils to verify exact wire gauge before ordering: count 20 tight, unweighted coils and measure to the nearest 1/16 inch ({twenty_coil_in}\" = {wire_in:.3f}\" wire; {ten_coil_in}\" over 10 coils). Being off by even one wire size changes lifting force by 25–35 lbs!",
            "Always replace BOTH Left-Wound and Right-Wound torsion springs at the same time: both springs were installed on the same day and endured the exact same number of cycles—the surviving spring will snap within weeks.",
            f"Use ONLY solid 1/2-inch diameter cold-rolled steel Winding Bars that fit snugly into the winding cone sockets ({quarter_turns} quarter-turns = {winding_turns} full turns for a {door_ht_ft}-foot door)—NEVER use screwdrivers, rebar, or ratchets, which snap under 200+ ft-lbs of stored torque.",
            "Disconnect the electric opener trolley and place a pair of Locking C-Clamps or Vise-Grips on the vertical track just above a bottom roller before loosening any winding cone set-screws."
        ],
        "faqs": [
            {
                "q": f"How much garage door weight does a {wire_in:.3f} × {id_in:g}\" × {len_in:g}\" torsion spring lift?",
                "a": f"Each {wire_in:.3f}\" × {id_in:g}\" × {len_in:g}\" spring has a torque rate of {ippt_single} IPPT (Inch-Pounds Per Turn). On standard 4-inch drums (2.0\" radius) wound to {winding_turns} turns ({door_ht_ft}-ft door), a single spring balances a {balanced_single_lbs}-lb door, and a matched pair balances a {balanced_pair_lbs}-lb door."
            },
            {
                "q": f"How many quarter-turns do I wind a torsion spring on a {door_ht_ft}-foot garage door?",
                "a": f"For a standard 7-foot tall door on 4-inch drums, wind each spring 7.5 full turns (30 quarter-turns). For an 8-foot tall door, wind each spring 8.5 full turns (34 quarter-turns). Paint a straight chalk line across the relaxed spring coils before winding so you can count full revolutions visually."
            },
            {
                "q": f"How do I measure my broken torsion spring to confirm it is {wire_in:.3f}\" wire?",
                "a": f"Do not measure a single wire strand with a tape measure! Instead, press 20 relaxed coils tightly together and measure from the 1st coil to the 20th coil. A 20-coil length of {twenty_coil_in} inches (or {ten_coil_in}\" across 10 coils) confirms {wire_in:.3f}-inch wire."
            }
        ]
    }


def generate_spring_data(spr_tuple):
    """
    LAPIS 2: Memanggil model Gemini stabil dengan proteksi Cooldown HTTP 429 & Fallback Otomatis.
    """
    if not GEMINI_API_KEY:
        return build_deterministic_spring_data(spr_tuple)

    item_name, wire_in, id_in, len_in, door_ht_ft, ref_door_lbs, color_code = spr_tuple
    det_fallback = build_deterministic_spring_data(spr_tuple)
    sp = det_fallback["specs"]

    prompt = f"""
You are a Certified IDEA / DASMA Master Garage Door Technician & Mechanical Spring Engineer. Create an accurate 2026 garage door torsion spring wire gauge (20-coil rule), IPPT torque rate, balanced door weight, and winding turn guide for: "{item_name}".
Baseline specs: Wire={wire_in}" ({sp['twenty_coil_length_in']}" across 20 coils, {color_code}), Inside Dia={id_in}", Length={len_in}" ({sp['active_coils']} active coils), Torque={sp['ippt_per_spring']} IPPT/spring ({sp['ippt_pair_total']} IPPT pair), Winding={sp['winding_full_turns']} turns ({sp['winding_quarter_turns']} quarter-turns for {door_ht_ft}ft door), Balanced Door Weight={sp['balanced_door_lbs_pair']} lbs (Pair) / {sp['balanced_door_lbs_single']} lbs (Single), High-Cycle Upgrade={sp['high_cycle_upgrade_spec']}.
Return ONLY a valid JSON object matching this exact schema:
{{
  "spring_name": "{item_name}",
  "color_code": "{color_code}",
  "seo_title": "{item_name} IPPT, Door Weight & Winding Turns Calculator (2026)",
  "meta_description": "Calculate exact IPPT torque, balanced garage door weight (lbs), 20-coil wire measurement, and winding bar quarter-turns for {item_name}.",
  "specs": {{
    "wire_diameter_in": {wire_in},
    "inside_diameter_in": {id_in},
    "spring_length_in": {len_in},
    "twenty_coil_length_in": {sp['twenty_coil_length_in']},
    "ten_coil_length_in": {sp['ten_coil_length_in']},
    "active_coils": {sp['active_coils']},
    "ippt_per_spring": {sp['ippt_per_spring']},
    "ippt_pair_total": {sp['ippt_pair_total']},
    "door_height_ft": {door_ht_ft},
    "winding_full_turns": {sp['winding_full_turns']},
    "winding_quarter_turns": {sp['winding_quarter_turns']},
    "balanced_door_lbs_pair": {sp['balanced_door_lbs_pair']},
    "balanced_door_lbs_single": {sp['balanced_door_lbs_single']},
    "high_cycle_upgrade_spec": "{sp['high_cycle_upgrade_spec']}",
    "color_code": "{color_code}"
  }},
  "dasma_verdict": "3-sentence technical summary stating 20-coil wire measurement, IPPT per spring, winding turns for a {door_ht_ft}-foot door, balanced door weight in lbs, and high-cycle upgrade dimensions.",
  "hardware_bundle": [
    {{
      "badge": "{wire_in:.3f} × {id_in:g}\" × {len_in:g}\" Pair",
      "title": "Matched Pair ({wire_in:.3f}\" × {id_in:g}\" × {len_in:g}\") Electrophoresis Torsion Springs + Winding Bars",
      "price_range": "$74 - $169",
      "amazon_query": "{wire_in:.3f} x {id_in:g} x {int(len_in)} Garage Door Torsion Springs Pair Winding Bars",
      "spr_note": "1-sentence left/right wound cones and winding bar note"
    }},
    {{
      "badge": "400-8 Drums & Lift Cables",
      "title": "Pair of 400-8 Aluminum Torsion Cable Drums + 1/8\" Aircraft Lift Cables & Center Bearing",
      "price_range": "$42 - $89",
      "amazon_query": "Garage Door 400-8 Cable Drums 1/8 Lift Cables Center Bearing",
      "spr_note": "1-sentence drum radius and cable safety note"
    }},
    {{
      "badge": "11-Ball Quiet Nylon Rollers",
      "title": "Sealed 6200ZZ 11-Ball Bearing Quiet Nylon Garage Door Rollers (12-Pack) + Lube",
      "price_range": "$34 - $69",
      "amazon_query": "Quiet Nylon Garage Door Rollers 6200ZZ 11 Ball Bearing",
      "spr_note": "1-sentence friction reduction and noise cut note"
    }},
    {{
      "badge": "Wall Jackshaft / Belt Opener",
      "title": "Wall-Mount Jackshaft or Ultra-Quiet Belt-Drive Smart Garage Door Opener",
      "price_range": "$229 - $579",
      "amazon_query": "Chamberlain LiftMaster Wall Mount Jackshaft Garage Door Opener",
      "spr_note": "1-sentence balanced torsion shaft operation note"
    }}
  ],
  "safety_checklist": [
    "Step 1 regarding 20-coil micrometer measurement ({sp['twenty_coil_length_in']} inches for {wire_in:.3f} wire)",
    "Step 2 regarding replacing both Left-Wound and Right-Wound springs simultaneously",
    "Step 3 regarding using 1/2-inch solid steel winding bars for {sp['winding_quarter_turns']} quarter-turns",
    "Step 4 regarding clamping the track and red set-screw torque (3/4 to 1 turn past finger-tight)"
  ],
  "faqs": [
    {{"q": "How much door weight does a pair of {item_name} balance?", "a": "Exact IPPT, turns, and door weight in lbs for single vs pair."}},
    {{"q": "How many turns do I wind {item_name}?", "a": "Exact full turns and quarter-turns for 7ft vs 8ft garage doors."}},
    {{"q": "How can I upgrade {item_name} to last 25,000+ cycles?", "a": "Exact high-cycle wire gauge and length conversion formula."}}
  ]
}}
"""

    for model_id in get_active_gemini_model(GEMINI_API_KEY):
        for attempt in range(2):
            try:
                endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent?key={GEMINI_API_KEY}"
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.2,
                        "responseMimeType": "application/json"
                    }
                }
                req = urllib.request.Request(
                    endpoint,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=40) as resp:
                    result = json.loads(resp.read().decode("utf-8"))
                    raw_text = result["candidates"][0]["content"]["parts"][0]["text"].strip()
                    raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
                    raw_text = re.sub(r"\s*```$", "", raw_text)
                    parsed = json.loads(raw_text)
                    if "specs" in parsed and "hardware_bundle" in parsed:
                        time.sleep(6)
                        return parsed
            except urllib.error.HTTPError as he:
                if he.code == 429:
                    print(f"[RATE-LIMIT] HTTP 429 on {model_id} (attempt {attempt + 1}). Cooling down 20s...")
                    time.sleep(20)
                else:
                    print(f"[WARN] HTTP {he.code} on {model_id} for '{item_name}': {he}")
                    break
            except Exception as e:
                print(f"[WARN] Gemini ({model_id}) notice for '{item_name}': {e}")
                break

    return det_fallback


def build_spring_html_page(data, slug, mon_cfg):
    spr_name = data.get("spring_name", "Garage Door Torsion Spring")
    sp = data.get("specs", {})
    wire_in = round(safe_float(sp.get("wire_diameter_in", 0.218), 0.218), 3)
    id_in = round(safe_float(sp.get("inside_diameter_in", 2.0), 2.0), 2)
    len_in = round(safe_float(sp.get("spring_length_in", 24.0), 24.0), 1)
    c20_in = round(safe_float(sp.get("twenty_coil_length_in", 4.36), 4.36), 2)
    ippt_1 = round(safe_float(sp.get("ippt_per_spring", 24.5), 24.5), 1)
    door_ht = int(safe_float(sp.get("door_height_ft", 7), 7))
    q_turns = int(safe_float(sp.get("winding_quarter_turns", 30), 30))
    pair_lbs = int(safe_float(sp.get("balanced_door_lbs_pair", 184), 184))
    hc_spec = sp.get("high_cycle_upgrade_spec", "0.225\" × 2\" × 28\"")
    c_code = sp.get("color_code", "DASMA Color Coded")

    header_cta = mon_cfg.get("header_cta", {})
    header_cta_url = build_amazon_url(header_cta.get("search_query", "Garage+Door+Torsion+Springs+Pair+Winding+Bars"), mon_cfg)

    schema_graph = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "SoftwareApplication",
                "name": f"{spr_name} IPPT, Door Weight & Winding Turns Calculator",
                "applicationCategory": "UtilitiesApplication",
                "operatingSystem": "Web Browser",
                "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"}
            },
            {
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": f.get("q", ""),
                        "acceptedAnswer": {"@type": "Answer", "text": f.get("a", "")}
                    } for f in data.get("faqs", [])
                ]
            }
        ]
    }

    bundle_html = ""
    for item in data.get("hardware_bundle", []):
        amz_url = build_amazon_url(item.get("amazon_query", item.get("title", "Garage Door Torsion Springs Pair")), mon_cfg)
        bundle_html += f"""
        <div class="bg-zinc-900 border border-zinc-800 rounded-xl p-5 flex flex-col justify-between hover:border-amber-500/60 transition">
          <div>
            <div class="flex items-center justify-between gap-2 mb-2">
              <span class="text-xs font-bold uppercase tracking-wider bg-amber-500/10 text-amber-400 border border-amber-500/20 px-2.5 py-0.5 rounded">{item.get('badge', 'Torsion Hardware')}</span>
              <span class="text-sm font-bold text-emerald-400">{item.get('price_range', '$42+')}</span>
            </div>
            <h3 class="text-base font-bold text-white mt-2">{item.get('title', '')}</h3>
            <p class="text-xs text-zinc-400 mt-2 leading-relaxed">🛠️ {item.get('spr_note', '')}</p>
          </div>
          <a href="{amz_url}" target="_blank" rel="nofollow sponsored" class="mt-5 block text-center bg-amber-500 hover:bg-amber-400 text-zinc-950 font-extrabold py-2.5 px-4 rounded-lg text-sm transition shadow-lg">
            Check Price on Amazon →
          </a>
        </div>"""

    # Build DASMA 20-Coil Wire Size Reference Matrix Table
    wire_tiers = [
        ("0.192\" Wire (Blue Tip)", "3.84\" (3-13/16\")", "1.92\" (1-15/16\")", "0.192 × 2\" × 20\"", "130 – 145 lb Door (Pair)"),
        ("0.207\" Wire (Yellow Tip)", "4.14\" (4-1/8\")", "2.07\" (2-1/16\")", "0.207 × 2\" × 22\"–24\"", "150 – 170 lb Door (Pair)"),
        ("0.218\" Wire (Red Tip)", "4.36\" (4-3/8\")", "2.18\" (2-3/16\")", "0.218 × 2\" × 23\"–26\"", "175 – 195 lb Door (Pair)"),
        ("0.225\" Wire (Brown/Purple)", "4.50\" (4-1/2\")", "2.25\" (2-1/4\")", "0.225 × 2\" × 24\"–28\"", "195 – 215 lb Door (Pair)"),
        ("0.234\" Wire (Orange/Green)", "4.68\" (4-11/16\")", "2.34\" (2-11/32\")", "0.234 × 2\" × 25\"–29\"", "220 – 245 lb Door (Pair)"),
        ("0.243\" Wire (Gold Tip)", "4.86\" (4-7/8\")", "2.43\" (2-7/16\")", "0.243 × 2\" × 26\"–30\"", "255 – 285 lb Door (Pair)"),
        ("0.250\" Wire (White/Blue)", "5.00\" (5-0\")", "2.50\" (2-1/2\")", "0.250 × 2\" × 28\"–32\"", "285 – 315 lb Door (Pair)")
    ]
    matrix_rows_html = ""
    for w_lbl, c20_lbl, c10_lbl, sp_lbl, wt_lbl in wire_tiers:
        matrix_rows_html += f"""
        <tr class="border-b border-zinc-800 hover:bg-zinc-800/40">
          <td class="py-3 px-4 font-bold text-white">{w_lbl}</td>
          <td class="py-3 px-4 font-bold text-amber-400">{c20_lbl}</td>
          <td class="py-3 px-4 text-zinc-300">{c10_lbl}</td>
          <td class="py-3 px-4 text-emerald-400 font-semibold">{sp_lbl}</td>
          <td class="py-3 px-4 text-xs text-zinc-300">{wt_lbl}</td>
        </tr>"""

    checklist_html = ""
    for idx, step_text in enumerate(data.get("safety_checklist", []), start=1):
        checklist_html += f"""
        <label class="flex items-start gap-3.5 bg-zinc-900 border border-zinc-800 rounded-xl p-4 cursor-pointer hover:border-zinc-700 transition">
          <input type="checkbox" class="mt-1 w-5 h-5 accent-amber-500 rounded cursor-pointer spr-check">
          <span class="text-sm text-zinc-200 leading-relaxed"><strong>DASMA Step {idx}:</strong> {step_text}</span>
        </label>"""

    faqs_html = "".join([
        f"<div class='bg-zinc-900 border border-zinc-800 rounded-xl p-5'><h3 class='font-bold text-white text-base mb-2'>{f.get('q', '')}</h3><p class='text-sm text-zinc-300 leading-relaxed'>{f.get('a', '')}</p></div>"
        for f in data.get("faqs", [])
    ])

    canonical_url = f"{SITE_BASE_URL}/{slug}.html"
    amz_domain = mon_cfg.get("marketplace_domain", "www.amazon.com")
    amz_tag = mon_cfg.get("amazon_associate_tag", "YOUR_AMAZON_TAG-20")

    html = f"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{data.get('seo_title', spr_name)}</title>
  <meta name="description" content="{data.get('meta_description', '')}">
  <link rel="canonical" href="{canonical_url}">
  <meta property="og:title" content="{data.get('seo_title', spr_name)}">
  <meta property="og:description" content="{data.get('meta_description', '')}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{canonical_url}">
  <script src="https://cdn.tailwindcss.com"></script>
  <script type="application/ld+json">{json.dumps(schema_graph)}</script>
</head>
<body class="bg-zinc-950 text-zinc-100 antialiased min-h-screen flex flex-col">
  <header class="border-b border-zinc-800 bg-zinc-900/80 backdrop-blur sticky top-0 z-30">
    <div class="max-w-5xl mx-auto px-4 py-3.5 flex items-center justify-between">
      <a href="index.html" class="text-lg font-black tracking-tight text-white flex items-center gap-2">
        <span class="bg-amber-500 text-zinc-950 px-2 py-0.5 rounded font-black">TORSION</span>SpringIndex
      </a>
      <a href="{header_cta_url}" target="_blank" rel="nofollow sponsored" class="text-xs sm:text-sm bg-amber-500 hover:bg-amber-400 text-zinc-950 font-extrabold px-3.5 py-2 rounded-lg transition">
        {header_cta.get('cta_text', 'Shop Torsion Springs & Winding Bars →')}
      </a>
    </div>
  </header>

  <main class="max-w-5xl mx-auto px-4 py-10 flex-1 w-full">
    <div class="mb-8">
      <div class="flex flex-wrap items-center gap-2.5 mb-3">
        <span class="text-xs font-extrabold uppercase tracking-widest bg-amber-500 text-zinc-950 px-3 py-1 rounded-full">{wire_in:.3f}" × {id_in:g}" × {len_in:g}" ({c_code})</span>
        <span class="text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-3 py-1 rounded-full">Balances {pair_lbs} lb Door (Pair) | {ippt_1} IPPT</span>
        <span class="text-xs font-semibold bg-zinc-800 text-zinc-300 px-3 py-1 rounded-full">20-Coil: {c20_in}" | Wind: {q_turns} Quarter-Turns</span>
      </div>
      <h1 class="text-3xl sm:text-4xl font-black text-white leading-tight">{data.get('seo_title', spr_name)}</h1>
      <div class="mt-4 bg-zinc-900 border-l-4 border-amber-500 p-4 rounded-r-xl text-sm text-zinc-200 leading-relaxed">
        <strong>DASMA Mechanical & IPPT Verdict:</strong> {data.get('dasma_verdict', '')}
      </div>
    </div>

    <!-- INTERACTIVE 20-COIL WIRE GAUGE, IPPT, DOOR WEIGHT & WINDING TURNS CALCULATOR -->
    <section class="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 sm:p-8 mb-12 shadow-2xl">
      <h2 class="text-xl font-extrabold text-white mb-2">Interactive {spr_name} IPPT, Door Weight & Turns Calculator</h2>
      <p class="text-xs text-zinc-400 mb-6">Select your 20-coil wire measurement, spring inside diameter, unweighted coil body length, and garage door height to calculate exact IPPT torque, balanced door weight, and winding bar quarter-turns.</p>

      <div class="grid md:grid-cols-2 gap-8 items-center">
        <div class="space-y-5">
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label for="wireSelect" class="block text-xs font-medium text-zinc-400 mb-1">Wire Size (20-Coil Length)</label>
              <select id="wireSelect" class="w-full bg-zinc-950 border border-zinc-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-500">
                <option value="0.192" {"selected" if wire_in <= 0.195 else ""}>0.192" (20 Coils = 3-13/16")</option>
                <option value="0.207" {"selected" if 0.195 < wire_in <= 0.210 else ""}>0.207" (20 Coils = 4-1/8")</option>
                <option value="0.218" {"selected" if 0.210 < wire_in <= 0.221 else ""}>0.218" (20 Coils = 4-3/8")</option>
                <option value="0.225" {"selected" if 0.221 < wire_in <= 0.229 else ""}>0.225" (20 Coils = 4-1/2")</option>
                <option value="0.234" {"selected" if 0.229 < wire_in <= 0.238 else ""}>0.234" (20 Coils = 4-11/16")</option>
                <option value="0.243" {"selected" if 0.238 < wire_in <= 0.246 else ""}>0.243" (20 Coils = 4-7/8")</option>
                <option value="0.250" {"selected" if 0.246 < wire_in <= 0.256 else ""}>0.250" (20 Coils = 5-0")</option>
                <option value="0.262" {"selected" if wire_in > 0.256 else ""}>0.262" (20 Coils = 5-1/4")</option>
              </select>
            </div>
            <div>
              <label for="idSelect" class="block text-xs font-medium text-zinc-400 mb-1">Inside Diameter & Door Ht</label>
              <select id="idSelect" class="w-full bg-zinc-950 border border-zinc-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-500">
                <option value="1.75|7.5" {"selected" if id_in < 1.9 else ""}>1.75" ID — 7 ft Door (7.5 Turns)</option>
                <option value="2.00|7.5" {"selected" if id_in >= 1.9 and door_ht == 7 else ""}>2.00" ID — 7 ft Door (7.5 Turns)</option>
                <option value="2.00|8.5" {"selected" if id_in >= 1.9 and door_ht >= 8 else ""}>2.00" ID — 8 ft Door (8.5 Turns)</option>
              </select>
            </div>
          </div>

          <div>
            <div class="flex justify-between text-sm font-medium mb-1.5">
              <label for="lenSlider" class="text-zinc-300">Unwound Spring Coil Body Length (Inches)</label>
              <span class="text-amber-400 font-bold"><span id="lenVal">{len_in:g}</span>" Length</span>
            </div>
            <input id="lenSlider" type="range" min="18" max="38" step="1" value="{int(len_in)}" class="w-full accent-amber-500 cursor-pointer">
          </div>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div class="bg-zinc-950 border border-amber-500/30 rounded-xl p-4">
            <span class="text-xs uppercase text-amber-400 font-bold">Balanced Door Weight</span>
            <div class="text-2xl sm:text-3xl font-black text-white mt-1"><span id="pairLbsOut">{pair_lbs}</span> <span class="text-xs font-normal text-zinc-400">lbs (Pair)</span></div>
            <p id="singleLbsOut" class="text-xs text-amber-400 font-semibold mt-1">Single Spring: {pair_lbs // 2} lbs ({ippt_1} IPPT)</p>
          </div>

          <div class="bg-zinc-950 border border-emerald-500/30 rounded-xl p-4">
            <span class="text-xs uppercase text-emerald-400 font-bold">Winding Bar Turns</span>
            <div class="text-2xl sm:text-3xl font-black text-emerald-400 mt-1"><span id="qTurnsOut">{q_turns}</span> <span class="text-xs font-normal text-zinc-400">1/4-Turns</span></div>
            <p id="hcSpecOut" class="text-xs text-zinc-300 font-semibold mt-1">High-Cycle: {hc_spec.split()[0]} Wire</p>
          </div>
        </div>
      </div>

      <div class="mt-6 bg-amber-950/40 border border-amber-500/30 rounded-xl p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div id="sprAdviceBanner" class="text-sm text-amber-100 font-medium"></div>
        <a id="dynamicSprBtn" href="{header_cta_url}" target="_blank" rel="nofollow sponsored" class="shrink-0 bg-amber-500 hover:bg-amber-400 text-zinc-950 font-extrabold px-4 py-2.5 rounded-lg text-xs uppercase tracking-wider transition">
          Shop Matched Torsion Spring Pair on Amazon →
        </a>
      </div>
    </section>

    <section class="mb-12">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-2xl font-extrabold text-white">Complete {spr_name} Springs, Winding Bars & Roller Bundle</h2>
        <span class="text-xs text-zinc-400">ASTM A229 Oil-Tempered & DASMA Rated</span>
      </div>
      <div class="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">{bundle_html}</div>
    </section>

    <section class="mb-12">
      <h2 class="text-2xl font-extrabold text-white mb-4">Garage Door Torsion Spring 20-Coil Wire Measurement, Color Code & Door Weight Chart</h2>
      <div class="overflow-x-auto bg-zinc-900 border border-zinc-800 rounded-xl">
        <table class="w-full text-left border-collapse text-sm">
          <thead>
            <tr class="border-b border-zinc-800 bg-zinc-950/60 text-zinc-400 uppercase text-xs">
              <th class="py-3.5 px-4">Wire Gauge & Color Code</th>
              <th class="py-3.5 px-4 text-amber-400">20-Coil Measurement</th>
              <th class="py-3.5 px-4">10-Coil Measurement</th>
              <th class="py-3.5 px-4 text-emerald-400">Common Spring Pair Size</th>
              <th class="py-3.5 px-4">Balanced Door Weight</th>
            </tr>
          </thead>
          <tbody>{matrix_rows_html}</tbody>
        </table>
      </div>
    </section>

    <section class="mb-12">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-2xl font-extrabold text-white">DASMA Torsion Spring Measurement & Winding Bar Safety Checklist</h2>
        <span id="sprBadge" class="text-xs font-bold bg-zinc-800 text-amber-400 px-3 py-1 rounded-full">0 / 4 Completed</span>
      </div>
      <div class="space-y-3">{checklist_html}</div>
    </section>

    <section class="mb-12">
      <h2 class="text-2xl font-extrabold text-white mb-5">Frequently Asked Questions ({spr_name})</h2>
      <div class="space-y-4">{faqs_html}</div>
    </section>
  </main>

  <footer class="border-t border-zinc-800 py-8 text-center text-xs text-zinc-500 px-4">
    <p>© {datetime.now(timezone.utc).year} TorsionSpringIndex. Independent DASMA Garage Door Counterbalance & IPPT Sizing Database. As an Amazon Associate, we earn from qualifying purchases.</p>
  </footer>

  <script>
    const amzDomain = "{amz_domain}";
    const amzTag = "{amz_tag}";

    const wireSelect = document.getElementById('wireSelect');
    const idSelect = document.getElementById('idSelect');
    const lenSlider = document.getElementById('lenSlider');
    const lenVal = document.getElementById('lenVal');
    const pairLbsOut = document.getElementById('pairLbsOut');
    const singleLbsOut = document.getElementById('singleLbsOut');
    const qTurnsOut = document.getElementById('qTurnsOut');
    const hcSpecOut = document.getElementById('hcSpecOut');
    const sprAdviceBanner = document.getElementById('sprAdviceBanner');
    const dynamicSprBtn = document.getElementById('dynamicSprBtn');

    function recalculateSpring() {{
      const wireDia = parseFloat(wireSelect.value);
      const idParts = idSelect.value.split('|');
      const idIn = parseFloat(idParts[0]);
      const fullTurns = parseFloat(idParts[1]);
      const lenIn = parseInt(lenSlider.value, 10);

      lenVal.textContent = lenIn;

      const activeCoils = lenIn / wireDia;
      const meanDia = idIn + wireDia;
      const ipptSingle = (30000000.0 * Math.pow(wireDia, 4)) / (3670.0 * meanDia * activeCoils);
      const pairDoorLbs = Math.round((2.0 * ipptSingle * fullTurns) / 2.0);
      const singleDoorLbs = Math.round(pairDoorLbs / 2.0);
      const qTurns = Math.round(fullTurns * 4);

      const hcWire = (wireDia + 0.012).toFixed(3);
      const hcLen = Math.round(lenIn * 1.26);

      pairLbsOut.textContent = pairDoorLbs;
      singleLbsOut.textContent = `Single: ${{singleDoorLbs}} lbs (${{ipptSingle.toFixed(1)}} IPPT)`;
      qTurnsOut.textContent = qTurns;
      hcSpecOut.textContent = `25k-Cycle: ${{hcWire}} × ${{hcLen}}"`;

      sprAdviceBanner.innerHTML = `🛠️ <strong>DASMA Replacement Spec:</strong> Order a <strong>Matched Pair (Left & Right Wound) of ${{wireDia.toFixed(3)}}" × ${{idIn}}" × ${{lenIn}}" Torsion Springs</strong> + <strong>1/2" Steel Winding Bars</strong> (wind exactly <strong>${{qTurns}} quarter-turns / ${{fullTurns}} full turns</strong> for a ${{pairDoorLbs}}-lb door).`;
      dynamicSprBtn.href = `https://${{amzDomain}}/s?k=${{wireDia.toFixed(3)}}+x+${{idIn}}+x+${{lenIn}}+Garage+Door+Torsion+Springs+Pair+Winding+Bars&tag=${{amzTag}}`;
    }}

    wireSelect.addEventListener('change', recalculateSpring);
    idSelect.addEventListener('change', recalculateSpring);
    lenSlider.addEventListener('input', recalculateSpring);
    recalculateSpring();

    const checks = document.querySelectorAll('.spr-check');
    const badge = document.getElementById('sprBadge');
    checks.forEach(ch => {{
      ch.addEventListener('change', () => {{
        const done = Array.from(checks).filter(c => c.checked).length;
        badge.textContent = `${{done}} / ${{checks.length}} Completed`;
      }});
    }});
  </script>
</body>
</html>"""

    os.makedirs(DOCS_DIR, exist_ok=True)
    with open(os.path.join(DOCS_DIR, f"{slug}.html"), "w", encoding="utf-8") as f:
        f.write(html)


def rebuild_portal_sitemap_and_rss(published, mon_cfg):
    header_cta = mon_cfg.get("header_cta", {})
    header_cta_url = build_amazon_url(header_cta.get("search_query", "Garage+Door+Torsion+Springs+Pair+Winding+Bars"), mon_cfg)

    cards_html = ""
    for item in reversed(published):
        cards_html += f"""
        <a href="{item['slug']}.html" class="block bg-zinc-900 border border-zinc-800 hover:border-amber-500/60 rounded-xl p-5 transition group">
          <div class="flex items-center justify-between mb-2">
            <span class="text-xs font-black uppercase bg-amber-500 text-zinc-950 px-2.5 py-0.5 rounded">{item.get('door_lbs', 185)} lb Door (Pair)</span>
            <span class="text-xs text-zinc-400">{item.get('ippt', 24.5)} IPPT | {item.get('q_turns', 30)} Q-Turns</span>
          </div>
          <h2 class="text-base font-bold text-white group-hover:text-amber-400 transition">{item['spring_name']}</h2>
          <p class="text-xs text-zinc-400 mt-2 line-clamp-2">{item['description']}</p>
          <span class="inline-block mt-4 text-xs font-extrabold text-amber-400">Calculate 20-Coil Wire, IPPT & Turns →</span>
        </a>"""

    index_html = f"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>TorsionSpringIndex — Garage Door Torsion Spring Wire Size, IPPT & Winding Turns Calculator (2026)</title>
  <meta name="description" content="Calculate exact garage door torsion spring 20-coil wire size, IPPT torque capacity, balanced door weight in lbs, winding bar quarter-turns, and 25,000-cycle upgrades for 0.192, 0.207, 0.218, 0.225, 0.234, 0.243, and 0.250 springs.">
  <link rel="canonical" href="{SITE_BASE_URL}/">
  <link rel="alternate" type="application/rss+xml" title="TorsionSpringIndex RSS Feed" href="{SITE_BASE_URL}/rss.xml">
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-zinc-950 text-zinc-100 min-h-screen flex flex-col">
  <header class="border-b border-zinc-800 bg-zinc-900/80 sticky top-0 z-30 backdrop-blur">
    <div class="max-w-5xl mx-auto px-4 py-3.5 flex items-center justify-between">
      <div class="text-lg font-black text-white flex items-center gap-2">
        <span class="bg-amber-500 text-zinc-950 px-2 py-0.5 rounded font-black">TORSION</span>SpringIndex
      </div>
      <a href="{header_cta_url}" target="_blank" rel="nofollow sponsored" class="text-xs sm:text-sm bg-amber-500 hover:bg-amber-400 text-zinc-950 font-extrabold px-3.5 py-2 rounded-lg transition">
        {header_cta.get('cta_text', 'Shop Torsion Springs & Winding Bars →')}
      </a>
    </div>
  </header>

  <main class="max-w-5xl mx-auto px-4 py-12 flex-1 w-full">
    <div class="text-center max-w-2xl mx-auto mb-10">
      <h1 class="text-3xl sm:text-5xl font-black text-white tracking-tight">Garage Door Torsion Spring Wire Size, IPPT & Winding Database</h1>
      <p class="text-zinc-400 mt-3 text-base sm:text-lg">Select your torsion spring dimensions or garage door size below to verify 20-coil wire gauge, balanced door weight in lbs, winding bar quarter-turns, and high-cycle upgrades.</p>
      <div class="mt-6">
        <input id="filterInput" type="text" placeholder="Search spring size or door (e.g. 0.207 x 2 x 22, 0.218 x 2 x 24, 0.225 x 2 x 26, 0.250, 16x7 Insulated Door...)" class="w-full bg-zinc-900 border border-zinc-700 rounded-xl px-4 py-3.5 text-sm text-white focus:outline-none focus:border-amber-500">
      </div>
    </div>

    <div id="sprGrid" class="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">{cards_html}</div>
  </main>

  <footer class="border-t border-zinc-800 py-8 text-center text-xs text-zinc-500">
    <p>© {datetime.now(timezone.utc).year} TorsionSpringIndex. As an Amazon Associate, we earn from qualifying purchases.</p>
  </footer>

  <script>
    const filterInput = document.getElementById('filterInput');
    const cards = Array.from(document.getElementById('sprGrid').children);
    filterInput.addEventListener('input', (e) => {{
      const q = e.target.value.toLowerCase();
      cards.forEach(c => {{
        c.style.display = c.textContent.toLowerCase().includes(q) ? 'block' : 'none';
      }});
    }});
  </script>
</body>
</html>"""

    os.makedirs(DOCS_DIR, exist_ok=True)
    with open(os.path.join(DOCS_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    urls_xml = f"""  <url>
    <loc>{SITE_BASE_URL}/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>\n"""

    for item in published:
        urls_xml += f"""  <url>
    <loc>{SITE_BASE_URL}/{item['slug']}.html</loc>
    <lastmod>{item.get('date', today)}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.9</priority>
  </url>\n"""

    with open(os.path.join(DOCS_DIR, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(f"""<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls_xml}</urlset>""")

    rss_items = ""
    for item in list(reversed(published))[:30]:
        rss_items += f"""    <item>
      <title>{item['title']}</title>
      <link>{SITE_BASE_URL}/{item['slug']}.html</link>
      <guid>{SITE_BASE_URL}/{item['slug']}.html</guid>
      <description>{item['description']}</description>
    </item>\n"""

    rss_xml = f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>TorsionSpringIndex Garage Door Torsion Spring & IPPT Database</title>
    <link>{SITE_BASE_URL}/</link>
    <description>Interactive Garage Door Torsion Spring Wire Size, IPPT Torque & Winding Turn Calculators</description>
    <atom:link href="{SITE_BASE_URL}/rss.xml" rel="self" type="application/rss+xml" />
    <atom:link href="https://pubsubhubbub.appspot.com/" rel="hub" />
{rss_items}  </channel>
</rss>"""

    with open(os.path.join(DOCS_DIR, "rss.xml"), "w", encoding="utf-8") as f:
        f.write(rss_xml)

    with open(os.path.join(DOCS_DIR, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {SITE_BASE_URL}/sitemap.xml\n")

    with open(os.path.join(DOCS_DIR, f"{INDEXNOW_KEY}.txt"), "w", encoding="utf-8") as f:
        f.write(INDEXNOW_KEY)


def notify_search_engines(new_urls):
    """Multi-Endpoint Search Engine Pinger (IndexNow Global + Bing + Google WebSub)."""
    if not SITE_BASE_URL or not new_urls:
        return
    parsed_host = urllib.parse.urlparse(SITE_BASE_URL).netloc
    payload = {
        "host": parsed_host,
        "key": INDEXNOW_KEY,
        "keyLocation": f"{SITE_BASE_URL}/{INDEXNOW_KEY}.txt",
        "urlList": new_urls
    }
    for idx_endpoint in ["https://api.indexnow.org/indexnow", "https://www.bing.com/indexnow"]:
        try:
            req = urllib.request.Request(
                idx_endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json; charset=utf-8"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                print(f"[INDEXNOW] Pushed {len(new_urls)} URLs to {idx_endpoint} (HTTP {resp.status})")
                break
        except Exception as e:
            print(f"[WARN] IndexNow ({idx_endpoint}) notice: {e}")

    try:
        hub_data = urllib.parse.urlencode({
            "hub.mode": "publish",
            "hub.url": f"{SITE_BASE_URL}/rss.xml"
        }).encode("utf-8")
        req_hub = urllib.request.Request(
            "https://pubsubhubbub.appspot.com/",
            data=hub_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST"
        )
        with urllib.request.urlopen(req_hub, timeout=15) as resp_hub:
            print(f"[WEBSUB] Google PubSubHubbub ping status: {resp_hub.status}")
    except Exception as e:
        print(f"[WARN] WebSub ping notice: {e}")


def main():
    published = load_json(PUBLISHED_FILE, [])
    mon_cfg = load_json(MONETIZATION_FILE, {})
    published_slugs = {item["slug"] for item in published if "slug" in item}

    candidates = []
    if CUSTOM_SPRING:
        candidates.append((CUSTOM_SPRING.strip(), 0.218, 2.00, 24.0, 7, 184, "Red Painted Tip"))
    candidates.extend(SEED_SPRINGS)
    candidates.extend(discover_google_spring_queries(published_slugs))

    new_urls = []
    count = 0

    for spr_tuple in candidates:
        if count >= PAGES_PER_RUN:
            break
        s_name = spr_tuple[0]
        slug = slugify(f"{s_name}-ippt-turns-calculator")
        if slug in published_slugs:
            continue

        print(f"[ENGINE] Generating garage door torsion spring IPPT & turns calculator for: {s_name}...")
        try:
            data = generate_spring_data(spr_tuple)
            build_spring_html_page(data, slug, mon_cfg)
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            sp = data.get("specs", {})

            published.append({
                "spring_name": data.get("spring_name", s_name),
                "slug": slug,
                "title": data.get("seo_title", f"{s_name} Torsion Spring Calculator"),
                "description": data.get("meta_description", ""),
                "door_lbs": int(safe_float(sp.get("balanced_door_lbs_pair", spr_tuple[5]), spr_tuple[5])),
                "ippt": round(safe_float(sp.get("ippt_per_spring", 24.5), 24.5), 1),
                "q_turns": int(safe_float(sp.get("winding_quarter_turns", 30), 30)),
                "date": today
            })
            published_slugs.add(slug)
            if SITE_BASE_URL:
                new_urls.append(f"{SITE_BASE_URL}/{slug}.html")
            count += 1
            if count < PAGES_PER_RUN:
                time.sleep(15)
        except Exception as e:
            print(f"[ERROR] Failed building {s_name}: {e}")

    save_json(PUBLISHED_FILE, published)
    rebuild_portal_sitemap_and_rss(published, mon_cfg)
    if new_urls and SITE_BASE_URL:
        new_urls.append(f"{SITE_BASE_URL}/")
        notify_search_engines(new_urls)
    print(f"[DONE] Published {count} new garage door torsion spring calculator pages.")


if __name__ == "__main__":
    main()
