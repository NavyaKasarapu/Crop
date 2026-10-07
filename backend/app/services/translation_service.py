import urllib.parse
import urllib.request
import json

# Comprehensive offline dictionary for English, Telugu, and Hindi agricultural terms
TRANSLATIONS = {
    "te": {
        "healthy": "ఆరోగ్యంగా ఉంది",
        "disease detected": "వ్యాధి గుర్తించబడింది",
        "unable to determine": "నిర్ధారించలేకపోయాము",
        "unknown": "తెలియదు",
        "unsupported": "మద్దతు లేదు",
        "unsupported image / crop": "మద్దతు లేని చిత్రం / పంట",
        "low": "తక్కువ",
        "medium": "మధ్యస్థ",
        "high": "అధిక",
        "none": "లేదు",
        "apple": "ఆపిల్",
        "blueberry": "బ్లూబెర్రీ",
        "cherry": "చెర్రీ",
        "corn": "మొక్కజొన్న",
        "grape": "ద్రాక్ష",
        "orange": "నారింజ",
        "peach": "పీచ్",
        "pepper": "బెల్ పెప్పర్ (మిరప)",
        "bell pepper": "బెల్ పెప్పర్ (మిరప)",
        "potato": "బంగాళాదుంప",
        "raspberry": "రాస్ప్‌బెర్రీ",
        "soybean": "సోయాబీన్",
        "squash": "స్క్వాష్",
        "strawberry": "స్ట్రాబెర్రీ",
        "tomato": "టమోటా",
        "apple scab": "ఆపిల్ స్కాబ్",
        "black rot": "నల్ల కుళ్ళు తెగులు",
        "cedar apple rust": "సెడార్ ఆపిల్ తుప్పు తెగులు",
        "powdery mildew": "బూడిద తెగులు",
        "common rust": "సాధారణ తుప్పు తెగులు",
        "gray leaf spot": "బూడిద రంగు ఆకుమచ్చ తెగులు",
        "northern leaf blight": "ఉత్తర ఆకు ఎండు తెగులు",
        "early blight": "ముందస్తు ఎండు తెగులు",
        "late blight": "ఆలస్యపు ఎండు తెగులు",
        "bacterial spot": "బ్యాక్టీరియల్ మచ్చ తెగులు",
        "leaf mold": "ఆకు బూజు తెగులు",
        "septoria leaf spot": "సెప్టోరియా ఆకుమచ్చ తెగులు",
        "spider mites": "ఎర్ర నల్లి తెగులు",
        "target spot": "టార్గెట్ స్పాట్ తెగులు",
        "yellow leaf curl virus": "ఆకు ముడుత వైరస్",
        "mosaic virus": "మొజాయిక్ వైరస్",
        "leaf scorch": "ఆకు మాడటం",
        "esca": "ఎస్కా (బ్లాక్ మీజిల్స్)",
        "citrus greening": "సిట్రస్ గ్రీనింగ్ తెగులు",
    },
    "hi": {
        "healthy": "स्वस्थ",
        "disease detected": "बीमारी पाई गई",
        "unable to determine": "निर्धारित नहीं किया जा सका",
        "unknown": "अज्ञात",
        "unsupported": "असमर्थित",
        "unsupported image / crop": "असमर्थित छवि / फसल",
        "low": "कम",
        "medium": "मध्यम",
        "high": "अधिक",
        "none": "कोई नहीं",
        "apple": "सेब",
        "blueberry": "ब्लूबेरी",
        "cherry": "चेरी",
        "corn": "मक्का",
        "grape": "अंगूर",
        "orange": "संतरा",
        "peach": "आड़ू",
        "pepper": "शिमला मिर्च",
        "bell pepper": "शिमला मिर्च",
        "potato": "आलू",
        "raspberry": "रसभरी",
        "soybean": "सोयाबीन",
        "squash": "कुम्हड़ा",
        "strawberry": "स्ट्रॉबेरी",
        "tomato": "टमाटर",
        "apple scab": "सेब स्कैब",
        "black rot": "काला सड़न रोग",
        "cedar apple rust": "देवदार सेब रतुआ",
        "powdery mildew": "चूर्णिल आसिता (सफेद फफूंद)",
        "common rust": "सामान्य रतुआ रोग",
        "gray leaf spot": "धूसर पत्ती धब्बा",
        "northern leaf blight": "उत्तरी पत्ती झुलसा",
        "early blight": "अगेती झुलसा",
        "late blight": "पछेती झुलसा",
        "bacterial spot": "जीवाणु धब्बा रोग",
        "leaf mold": "पत्ती फफूंद",
        "septoria leaf spot": "सेप्टोरिया पत्ती धब्बा",
        "spider mites": "लाल मकड़ी कीट",
        "target spot": "टारगेट स्पॉट रोग",
        "yellow leaf curl virus": "पीला पत्ता मरोड़ वायरस",
        "mosaic virus": "मोज़ेक वायरस",
        "leaf scorch": "पत्ती झुलसन",
        "esca": "एस्का रोग",
        "citrus greening": "सिट्रस ग्रीनिंग रोग",
    }
}


from pathlib import Path

class TranslationService:
    def __init__(self):
        data_dir = Path(__file__).resolve().parent.parent / "data"
        self.hi_json_path = data_dir / "translations_hi.json"
        self.te_json_path = data_dir / "translations_te.json"

        if self.hi_json_path.exists():
            try:
                with open(self.hi_json_path, "r", encoding="utf-8") as f:
                    hi_data = json.load(f)
                    for k, v in hi_data.items():
                        TRANSLATIONS["hi"][k.lower().strip()] = v
                        TRANSLATIONS["hi"][k.strip()] = v
            except Exception as e:
                print(f"[TranslationService] Warning loading translations_hi.json: {e}")

        if self.te_json_path.exists():
            try:
                with open(self.te_json_path, "r", encoding="utf-8") as f:
                    te_data = json.load(f)
                    for k, v in te_data.items():
                        TRANSLATIONS["te"][k.lower().strip()] = v
                        TRANSLATIONS["te"][k.strip()] = v
            except Exception as e:
                print(f"[TranslationService] Warning loading translations_te.json: {e}")

    def translate_phrase(self, text: str, target_lang: str) -> str:
        lang = target_lang.lower().strip()
        if lang == "en" or not text:
            return text

        clean = text.lower().strip()
        dict_for_lang = TRANSLATIONS.get(lang, {})
        
        # 1. Exact match (case-sensitive and lowercase)
        if text.strip() in dict_for_lang:
            return dict_for_lang[text.strip()]
        if clean in dict_for_lang:
            return dict_for_lang[clean]

        # 2. Check if text without trailing period matches
        if clean.endswith(".") and clean[:-1].strip() in dict_for_lang:
            return dict_for_lang[clean[:-1].strip()] + "।"

        # 3. Check partial dictionary replacement
        for k, v in dict_for_lang.items():
            if len(k) > 3 and k in clean:
                if len(k) >= len(clean) * 0.7:
                    return v

        # Online fallback using MyMemory public API with short timeout
        try:
            encoded_text = urllib.parse.quote(text[:500])
            url = f"https://api.mymemory.translated.net/get?q={encoded_text}&langpair=en|{lang}"
            req = urllib.request.Request(url, headers={"User-Agent": "CropDiseaseAI/1.0"})
            with urllib.request.urlopen(req, timeout=2.5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                translated = data.get("responseData", {}).get("translatedText")
                if translated and not translated.startswith("MYMEMORY WARNING"):
                    return translated
        except Exception:
            pass

        # Return original text gracefully if translation fails
        return text

    def translate(self, text: str, target_lang: str) -> str:
        return self.translate_phrase(text, target_lang)

    def translate_list(self, items: list, target_lang: str) -> list:
        if target_lang == "en" or not items:
            return items
        return [self.translate(item, target_lang) for item in items]


translation_service = TranslationService()
