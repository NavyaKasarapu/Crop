import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DATA_DIR = Path(__file__).resolve().parent
KNOWLEDGE_FILE = DATA_DIR / "disease_knowledge.json"
OUTPUT_HI = DATA_DIR / "translations_hi.json"
OUTPUT_TE = DATA_DIR / "translations_te.json"

with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
    knowledge = json.load(f)

# Load existing translations if present to cache
existing_hi = {}
if OUTPUT_HI.exists():
    try:
        with open(OUTPUT_HI, "r", encoding="utf-8") as f:
            existing_hi = json.load(f)
    except Exception:
        pass

existing_te = {}
if OUTPUT_TE.exists():
    try:
        with open(OUTPUT_TE, "r", encoding="utf-8") as f:
            existing_te = json.load(f)
    except Exception:
        pass

# Collect all phrases across all 38 classes
phrases = set()

# Standard crops, conditions, statuses, UI terms
standard_terms = [
    # Crops
    "Apple", "Blueberry", "Cherry", "Cherry (including sour)", "Corn", "Corn (maize)",
    "Grape", "Orange", "Peach", "Pepper", "Bell Pepper", "Pepper, bell", "Potato",
    "Raspberry", "Soybean", "Squash", "Strawberry", "Tomato",
    "Unsupported Image / Crop", "Unsupported", "Unknown", "Healthy", "Disease Detected",
    "Unable to determine", "None", "Low", "Medium", "High", "N/A", "Direct", "Estimated",
    "Leaf surface lesion ratio", "Overall vigor index", "Class probability",
    "Healthy foliage", "No lesions detected", "Unsupported image",
    "Leaf Health Observation", "Symptoms & Visual Indicators",
    "Crop Health Assessment", "Possible Causes & Pathogen Background",
    "Recommended Crop Care & Maintenance", "Actionable Recommendations",
    "Preventive Cultural Practices", "Prevention & Cultural Practices",
    "No disease symptoms detected on the foliage.",
    "Normal healthy leaf coloration and cellular structure observed across foliage.",
    "The uploaded image could not be matched to any of the 14 supported crop leaf varieties with sufficient confidence.",
    "Take a clear, well-lit photo of a single crop leaf filling the center of the frame.",
    "Avoid blurry images, severe glare, dark shadows, or complex background objects.",
    "Supported crops: Apple, Blueberry, Cherry, Corn, Grape, Orange, Peach, Bell Pepper, Potato, Raspberry, Soybean, Squash, Strawberry, and Tomato.",
    "Photograph individual leaves against a neutral, high-contrast background for highest accuracy.",
    "Upload a clear, focused photo of a leaf from one of the 14 supported crops.",
    "Ensure adequate lighting and make sure the leaf fills the majority of the image frame.",
    "Image does not match any of the 14 supported crops.",
    "The uploaded photo is either not a crop leaf, or the plant species is outside the 14 supported crops.",
    "Estimated (Computer Vision Leaf Area Analysis)",
    "Estimated (LLRL HLFA-Net + Lesion Analysis)",
    "Healthy Leaf Baseline"
]

for t in standard_terms:
    phrases.add(t)

for cls_name, cls_info in knowledge.items():
    if cls_info.get("crop_name"):
        phrases.add(cls_info["crop_name"])
    if cls_info.get("disease_name"):
        phrases.add(cls_info["disease_name"])
    if cls_info.get("cause"):
        phrases.add(cls_info["cause"])
    for s in cls_info.get("symptoms", []):
        if s:
            phrases.add(s)
    for r in cls_info.get("recommendations", []):
        if r:
            phrases.add(r)
    for p in cls_info.get("prevention", []):
        if p:
            phrases.add(p)

print(f"Total unique phrases to translate: {len(phrases)}")

def translate_gtx(text, target_lang):
    if not text:
        return text
    encoded = urllib.parse.quote(text)
    url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl={target_lang}&dt=t&q={encoded}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        translated = "".join(part[0] for part in data[0] if part[0])
        return translated

# Curated crop and disease terms for highest natural accuracy in Telugu
TELUGU_SPECIAL = {
    "Apple": "ఆపిల్",
    "Blueberry": "బ్లూబెర్రీ",
    "Cherry": "చెర్రీ",
    "Cherry (including sour)": "చెర్రీ",
    "Corn": "మొక్కజొన్న",
    "Corn (maize)": "మొక్కజొన్న",
    "Grape": "ద్రాక్ష",
    "Orange": "నారింజ",
    "Peach": "పీచ్",
    "Pepper": "బెల్ పెప్పర్ (మిరప)",
    "Bell Pepper": "బెల్ పెప్పర్ (మిరప)",
    "Pepper, bell": "బెల్ పెప్పర్ (మిరప)",
    "Potato": "బంగాళాదుంప",
    "Raspberry": "రాస్ప్‌బెర్రీ",
    "Soybean": "సోయాబీన్",
    "Squash": "స్క్వాష్ (గుమ్మడి)",
    "Strawberry": "స్ట్రాబెర్రీ",
    "Tomato": "టమోటా",
    "Healthy": "ఆరోగ్యంగా ఉంది",
    "Disease Detected": "వ్యాధి గుర్తించబడింది",
    "Unsupported Image / Crop": "మద్దతు లేని చిత్రం / పంట",
    "Unsupported": "మద్దతు లేదు",
    "Unknown": "తెలియదు",
    "Unable to determine": "నిర్ధారించలేకపోయాము",
    "None": "లేదు",
    "Low": "తక్కువ",
    "Medium": "మధ్యస్థం",
    "High": "తీవ్రం",
    "N/A": "వర్తించదు",
    "Apple Scab": "ఆపిల్ స్కాబ్",
    "Black Rot": "నల్ల కుళ్ళు తెగులు",
    "Cedar Apple Rust": "సెడార్ ఆపిల్ తుప్పు తెగులు",
    "Powdery Mildew": "బూడిద తెగులు",
    "Common Rust": "సాధారణ తుప్పు తెగులు",
    "Cercospora Leaf Spot / Gray Leaf Spot": "బూడిద రంగు ఆకుమచ్చ తెగులు (సెర్కోస్పోరా)",
    "Northern Leaf Blight": "ఉత్తర ఆకు ఎండు తెగులు",
    "Esca (Black Measles)": "ఎస్కా (బ్లాక్ మీజిల్స్)",
    "Leaf Blight (Isariopsis Leaf Spot)": "ఆకు ఎండు తెగులు (ఇసారియోప్సిస్)",
    "Huanglongbing (Citrus Greening)": "సిట్రస్ గ్రీనింగ్ తెగులు (హువాంగ్‌లాంగ్‌బింగ్)",
    "Bacterial Spot": "బ్యాక్టీరియల్ మచ్చ తెగులు",
    "Early Blight": "ముందస్తు ఎండు తెగులు (ఎర్లీ బ్లైట్)",
    "Late Blight": "ఆలస్యపు ఎండు తెగులు (లేట్ బ్లైట్)",
    "Leaf Mold": "ఆకు బూజు తెగులు",
    "Septoria Leaf Spot": "సెప్టోరియా ఆకుమచ్చ తెగులు",
    "Spider Mites (Two-spotted spider mite)": "ఎర్ర నల్లి తెగులు",
    "Target Spot": "టార్గెట్ స్పాట్ తెగులు",
    "Tomato Yellow Leaf Curl Virus": "టమోటా పసుపు ఆకు ముడుత వైరస్",
    "Tomato Mosaic Virus": "టమోటా మొజాయిక్ వైరస్",
    "Leaf Scorch": "ఆకు మాడటం తెగులు",
}

# Curated crop and disease terms for Hindi
HINDI_SPECIAL = {
    "Apple": "सेब",
    "Blueberry": "ब्लूबेरी",
    "Cherry": "चेरी",
    "Cherry (including sour)": "चेरी",
    "Corn": "मक्का",
    "Corn (maize)": "मक्का",
    "Grape": "अंगूर",
    "Orange": "संतरा",
    "Peach": "आड़ू",
    "Pepper": "शिमला मिर्च",
    "Bell Pepper": "शिमला मिर्च",
    "Pepper, bell": "शिमला मिर्च",
    "Potato": "आलू",
    "Raspberry": "रसभरी",
    "Soybean": "सोयाबीन",
    "Squash": "कुम्हड़ा (कद्दू)",
    "Strawberry": "स्ट्रॉबेरी",
    "Tomato": "टमाटर",
    "Healthy": "स्वस्थ",
    "Disease Detected": "बीमारी पाई गई",
    "Unsupported Image / Crop": "असमर्थित छवि / फसल",
    "Unsupported": "असमर्थित",
    "Unknown": "अज्ञात",
    "Unable to determine": "निर्धारित नहीं किया जा सका",
    "None": "कोई नहीं",
    "Low": "कम",
    "Medium": "मध्यम",
    "High": "अधिक",
    "N/A": "लागू नहीं",
    "Apple Scab": "सेब स्कैब",
    "Black Rot": "काला सड़न रोग",
    "Cedar Apple Rust": "देवदार सेब रतुआ",
    "Powdery Mildew": "चूर्णिल आसिता (सफेद फफूंद)",
    "Common Rust": "सामान्य रतुआ रोग",
    "Cercospora Leaf Spot / Gray Leaf Spot": "धूसर पत्ती धब्बा (सर्कोस्पोरा)",
    "Northern Leaf Blight": "उत्तरी पत्ती झुलसा",
    "Esca (Black Measles)": "एस्का रोग (काला खसरा)",
    "Leaf Blight (Isariopsis Leaf Spot)": "पत्ती झुलसा रोग (इसारिओप्सिस)",
    "Huanglongbing (Citrus Greening)": "सिट्रस ग्रीनिंग रोग (हुआंगलोंगबिंग)",
    "Bacterial Spot": "जीवाणु धब्बा रोग",
    "Early Blight": "अगेती झुलसा रोग",
    "Late Blight": "पछेती झुलसा रोग",
    "Leaf Mold": "पत्ती फफूंद (लीफ मोल्ड)",
    "Septoria Leaf Spot": "सेप्टोरिया पत्ती धब्बा",
    "Spider Mites (Two-spotted spider mite)": "लाल मकड़ी कीट",
    "Target Spot": "टारगेट स्पॉट रोग",
    "Tomato Yellow Leaf Curl Virus": "टमाटर पीला पत्ता मरोड़ वायरस",
    "Tomato Mosaic Virus": "टमाटर मोज़ेक वायरस",
    "Leaf Scorch": "पत्ती झुलसन",
}

hi_dict = dict(existing_hi)
te_dict = dict(existing_te)

# Apply special curated
hi_dict.update(HINDI_SPECIAL)
te_dict.update(TELUGU_SPECIAL)

phrase_list = sorted(list(phrases))
count_hi = 0
count_te = 0

print("Translating missing phrases to Hindi and Telugu...")
for i, phrase in enumerate(phrase_list):
    # Check Hindi
    if phrase not in hi_dict:
        try:
            hi_dict[phrase] = translate_gtx(phrase, "hi")
            count_hi += 1
            time.sleep(0.05)
        except Exception as e:
            print(f"HI failed for '{phrase[:30]}...': {e}")
            time.sleep(0.5)

    # Check Telugu
    if phrase not in te_dict:
        try:
            te_dict[phrase] = translate_gtx(phrase, "te")
            count_te += 1
            time.sleep(0.05)
        except Exception as e:
            print(f"TE failed for '{phrase[:30]}...': {e}")
            time.sleep(0.5)

    if (i + 1) % 50 == 0 or (i + 1) == len(phrase_list):
        print(f"Processed {i + 1}/{len(phrase_list)} phrases...")

with open(OUTPUT_HI, "w", encoding="utf-8") as f:
    json.dump(hi_dict, f, ensure_ascii=False, indent=2)

with open(OUTPUT_TE, "w", encoding="utf-8") as f:
    json.dump(te_dict, f, ensure_ascii=False, indent=2)

print(f"Successfully saved {len(hi_dict)} Hindi translations and {len(te_dict)} Telugu translations!")
