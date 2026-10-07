import { useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { generateSpeech, translateText, translateTexts } from "../services/api";
import "./Result.css";

const STORAGE_KEY = "cropDiseaseAnalyses";

const UI_TEXT = {
  en: {
    title: "Diagnostic Assessment",
    subtitle: "Automated plant health report from leaf image",
    language: "Language",
    crop: "CROP",
    condition: "CONDITION",
    diseaseIdentified: "DISEASE IDENTIFIED",
    confidence: "CONFIDENCE",
    classProbability: "Class probability",
    severityLevel: "SEVERITY LEVEL",
    affectedArea: "AFFECTED AREA",
    healthScore: "HEALTH SCORE",
    voiceAssistant: "Voice Assistant",
    voiceSubtitle: "Listen to complete report from top to bottom according to your choice",
    readingScope: "Reading Scope:",
    fullReport: "Full Report (Top to Bottom)",
    summaryOnly: "Summary (Crop, Disease & Severity)",
    actionsOnly: "Treatment & Prevention Only",
    readAloud: "▶ Read Aloud",
    resume: "▶ Resume",
    pause: "⏸ Pause",
    stop: "⏹ Stop",
    synthesizingAudio: "⏳ Synthesizing Audio...",
    leafHealthObs: "Leaf Health Observation",
    symptomsTitle: "Symptoms & Visual Indicators",
    healthySymptomsText: "Normal healthy leaf coloration and cellular structure observed across foliage.",
    noSymptomsText: "No specific symptom records available for this observation.",
    cropHealthAssessment: "Crop Health Assessment",
    causesTitle: "Possible Causes & Pathogen Background",
    recommendedCare: "Recommended Crop Care & Maintenance",
    recommendationsTitle: "Actionable Recommendations",
    preventivePractices: "Preventive Cultural Practices",
    preventionTitle: "Prevention & Cultural Practices",
    unsupportedTitle: "Unsupported Image / Crop",
    unsupportedDesc: "The uploaded image could not be matched to any of the 14 supported crop leaf varieties with sufficient confidence.",
    guidanceHeading: "Guidance for accurate results:",
    guidance1: "Take a clear, well-lit photo of a single crop leaf filling the center of the frame.",
    guidance2: "Avoid blurry images, severe glare, dark shadows, or complex background objects.",
    guidance3: "Supported crops: Apple, Blueberry, Cherry, Corn, Grape, Orange, Peach, Bell Pepper, Potato, Raspberry, Soybean, Squash, Strawberry, and Tomato.",
    analyzeAnother: "🔬 Analyze Another Leaf",
    viewDashboard: "📊 View Dashboard",
    viewHistory: "📜 View History",
    backHome: "🏠 Back to Home",
    diagnosticModel: "Diagnostic Model:",
    healthyFoliage: "Healthy foliage",
    unsupportedImage: "Unsupported Image",
    estimatedLesion: "Estimated (Lesion Area)",
    directAssessment: "Direct Assessment",
    noLesions: "No lesions detected",
    surfaceLesionRatio: "Leaf surface lesion ratio",
    vigorIndex: "Overall vigor index",
    notAvailable: "Not available",
    notAvailableModel: "Not available with current model",
    none: "None",
    healthy: "Healthy",
  },
  hi: {
    title: "रोग निदान मूल्यांकन",
    subtitle: "पत्ती की छवि से स्वचालित पादप स्वास्थ्य रिपोर्ट",
    language: "भाषा",
    crop: "फसल",
    condition: "स्थिति",
    diseaseIdentified: "पहचानी गई बीमारी",
    confidence: "सटीकता / विश्वास",
    classProbability: "वर्ग संभावना",
    severityLevel: "गंभीरता स्तर",
    affectedArea: "प्रभावित क्षेत्र",
    healthScore: "स्वास्थ्य स्कोर",
    voiceAssistant: "आवाज़ सहायक",
    voiceSubtitle: "अपनी पसंद के अनुसार पूरी रिपोर्ट शुरू से अंत तक सुनें",
    readingScope: "पठन दायरा:",
    fullReport: "पूरी रिपोर्ट (शुरू से अंत तक)",
    summaryOnly: "सारांश (फसल, बीमारी और गंभीरता)",
    actionsOnly: "केवल उपचार और रोकथाम",
    readAloud: "▶ पढ़कर सुनाएं",
    resume: "▶ पुनः आरंभ करें",
    pause: "⏸ रोकें",
    stop: "⏹ बंद करें",
    synthesizingAudio: "⏳ आवाज़ तैयार हो रही है...",
    leafHealthObs: "पत्ती स्वास्थ्य अवलोकन",
    symptomsTitle: "लक्षण और दृश्य संकेतक",
    healthySymptomsText: "पत्तियों में सामान्य स्वस्थ रंग और कोशिकीय संरचना देखी गई।",
    noSymptomsText: "इस अवलोकन के लिए कोई विशिष्ट लक्षण उपलब्ध नहीं हैं।",
    cropHealthAssessment: "फसल स्वास्थ्य मूल्यांकन",
    causesTitle: "संभावित कारण और रोगजनक पृष्ठभूमि",
    recommendedCare: "अनुशंसित फसल देखभाल और रखरखाव",
    recommendationsTitle: "कार्रवाई योग्य सलाह व उपचार",
    preventivePractices: "निवारक कृषि पद्धतियाँ",
    preventionTitle: "रोकथाम और कृषि पद्धतियाँ",
    unsupportedTitle: "असमर्थित छवि / फसल",
    unsupportedDesc: "अपलोड की गई छवि पर्याप्त विश्वास के साथ 14 समर्थित फसल किस्मों में से किसी से मेल नहीं खा सकी।",
    guidanceHeading: "सटीक परिणामों के लिए मार्गदर्शन:",
    guidance1: "फ्रेम के केंद्र में केवल एक फसल पत्ती की स्पष्ट और अच्छी रोशनी वाली तस्वीर लें।",
    guidance2: "धुंधली छवियों, तेज चकाचौंध, गहरे साये या जटिल पृष्ठभूमि वाली वस्तुओं से बचें।",
    guidance3: "समर्थित फसलें: सेब, ब्लूबेरी, चेरी, मक्का, अंगूर, संतरा, आड़ू, शिमला मिर्च, आलू, रसभरी, सोयाबीन, कुम्हड़ा, स्ट्रॉबेरी और टमाटर।",
    analyzeAnother: "🔬 दूसरी पत्ती का विश्लेषण करें",
    viewDashboard: "📊 डैशबोर्ड देखें",
    viewHistory: "📜 इतिहास देखें",
    backHome: "🏠 होम पेज पर जाएं",
    diagnosticModel: "निदान मॉडल:",
    healthyFoliage: "स्वस्थ पत्तियां",
    unsupportedImage: "असमर्थित छवि",
    estimatedLesion: "अनुमानित (घाव क्षेत्र)",
    directAssessment: "प्रत्यक्ष मूल्यांकन",
    noLesions: "कोई घाव नहीं पाया गया",
    surfaceLesionRatio: "पत्ती की सतह पर घाव का अनुपात",
    vigorIndex: "समग्र स्वास्थ्य सूचकांक",
    notAvailable: "उपलब्ध नहीं",
    notAvailableModel: "वर्तमान मॉडल के साथ उपलब्ध नहीं",
    none: "कोई नहीं",
    healthy: "स्वस्थ",
  },
  te: {
    title: "వ్యాధి నిర్ధారణ నివేదిక",
    subtitle: "ఆకు చిత్రం నుండి స్వయంచాలక మొక్కల ఆరోగ్య నివేదిక",
    language: "భాష",
    crop: "పంట",
    condition: "పరిస్థితి",
    diseaseIdentified: "గుర్తించిన వ్యాధి",
    confidence: "ఖచ్చితత్వం / విశ్వసనీయత",
    classProbability: "వర్గ సంభావ్యత",
    severityLevel: "తీవ్రత స్థాయి",
    affectedArea: "ప్రభావిత ప్రాంతం",
    healthScore: "ఆరోగ్య స్కోర్",
    voiceAssistant: "వాయిస్ అసిస్టెంట్",
    voiceSubtitle: "మీ ఎంపిక ప్రకారం మొత్తం నివేదికను పై నుండి క్రింది వరకు వినండి",
    readingScope: "వినే విధానం:",
    fullReport: "పూర్తి నివేదిక (పై నుండి క్రింది వరకు)",
    summaryOnly: "సారాంశం (పంట, వ్యాధి & తీవ్రత)",
    actionsOnly: "చికిత్స & నివారణ మాత్రమే",
    readAloud: "▶ చదివి వినిపించండి",
    resume: "▶ కొనసాగించండి",
    pause: "⏸ పాజ్",
    stop: "⏹ ఆపండి",
    synthesizingAudio: "⏳ ఆడియో రూపొందుతోంది...",
    leafHealthObs: "ఆకు ఆరోగ్య పరిశీలన",
    symptomsTitle: "లక్షణాలు & దృశ్య సూచికలు",
    healthySymptomsText: "ఆకులపై సాధారణ ఆరోగ్యకరమైన రంగు మరియు కణ నిర్మాణం గమనించబడింది.",
    noSymptomsText: "ఈ పరిశీలనకు నిర్దిష్ట లక్షణ రికార్డులు అందుబాటులో లేవు.",
    cropHealthAssessment: "పంట ఆరోగ్య అంచనా",
    causesTitle: "సాధ్యమయ్యే కారణాలు & వ్యాధికారక నేపథ్యం",
    recommendedCare: "సిఫార్సు చేసిన పంట సంరక్షణ & నిర్వహణ",
    recommendationsTitle: "ఆచరణాత్మక సిఫార్సులు & చికిత్స",
    preventivePractices: "నివారణ వ్యవసాయ పద్ధతులు",
    preventionTitle: "నివారణ & వ్యవసాయ పద్ధతులు",
    unsupportedTitle: "మద్దతు లేని చిత్రం / పంట",
    unsupportedDesc: "అప్‌లోడ్ చేసిన చిత్రం తగినంత ఖచ్చితత్వంతో మద్దతు ఉన్న 14 పంట ఆకు రకాలలో దేనికీ సరిపోలలేదు.",
    guidanceHeading: "ఖచ్చితమైన ఫలితాల కోసం సూచనలు:",
    guidance1: "ఫ్రేమ్ మధ్యలో ఒకే పంట ఆకు స్పష్టంగా మరియు మంచి వెలుతురులో కనిపించేలా ఫోటో తీయండి.",
    guidance2: "మసకగా ఉన్న చిత్రాలు, మిరుమిట్లు గొలిపే కాంతి, చీకటి నీడలు లేదా సంక్లిష్ట నేపథ్యాలను నివారించండి.",
    guidance3: "మద్దతు ఉన్న పంటలు: ఆపిల్, బ్లూబెర్రీ, చెర్రీ, మొక్కజొన్న, ద్రాక్ష, నారింజ, పీచ్, బెల్ పెప్పర్ (మిరప), బంగాళాదుంప, రాస్ప్‌బెర్రీ, సోయాబీన్, స్క్వాష్, స్ట్రాబెర్రీ, మరియు టమోటా.",
    analyzeAnother: "🔬 మరొక ఆకును విశ్లేషించండి",
    viewDashboard: "📊 డ్యాష్‌బోర్డ్ చూడండి",
    viewHistory: "📜 చరిత్ర చూడండి",
    backHome: "🏠 హోమ్ పేజీకి వెళ్ళండి",
    diagnosticModel: "డయాగ్నస్టిక్ మోడల్:",
    healthyFoliage: "ఆరోగ్యకరమైన ఆకులు",
    unsupportedImage: "మద్దతు లేని చిత్రం",
    estimatedLesion: "అంచనా (గాయం వైశాల్యం)",
    directAssessment: "ప్రత్యక్ష అంచనా",
    noLesions: "ఎలాంటి మచ్చలు కనిపించలేదు",
    surfaceLesionRatio: "ఆకు ఉపరితల గాయం నిష్పత్తి",
    vigorIndex: "మొత్తం ఆరోగ్య సూచిక",
    notAvailable: "అందుబాటులో లేదు",
    notAvailableModel: "ప్రస్తుత మోడల్‌తో అందుబాటులో లేదు",
    none: "లేదు",
    healthy: "ఆరోగ్యంగా ఉంది",
  }
};

function Result() {
  const location = useLocation();
  const navigate = useNavigate();

  const image = location.state?.image;
  const fileName = location.state?.fileName;
  const prediction = location.state?.prediction;
  const rawSeverity = location.state?.severity;
  const rawDiseaseInfo = location.state?.disease_info;

  // Multilingual UI state
  const [selectedLanguage, setSelectedLanguage] = useState("en");
  const [translating, setTranslating] = useState(false);

  // Translated display fields
  const [displayCrop, setDisplayCrop] = useState(prediction?.crop || "Unknown");
  const [displayCondition, setDisplayCondition] = useState(prediction?.condition || "Unknown");
  const [displayDisease, setDisplayDisease] = useState(prediction?.disease || "Unknown");
  const [displaySeverity, setDisplaySeverity] = useState(rawSeverity?.severity || "None");
  const [displaySymptoms, setDisplaySymptoms] = useState(
    Array.isArray(rawDiseaseInfo?.symptoms) ? rawDiseaseInfo.symptoms : []
  );
  const [displayCauses, setDisplayCauses] = useState(rawDiseaseInfo?.causes || "");
  const [displayRecommendations, setDisplayRecommendations] = useState(
    Array.isArray(rawDiseaseInfo?.recommendations) ? rawDiseaseInfo.recommendations : []
  );
  const [displayPrevention, setDisplayPrevention] = useState(
    Array.isArray(rawDiseaseInfo?.prevention) ? rawDiseaseInfo.prevention : []
  );

  const t = (key) => {
    return UI_TEXT[selectedLanguage]?.[key] || UI_TEXT.en[key] || "";
  };

  // Audio / Speech Queue State
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [isLoadingVoice, setIsLoadingVoice] = useState(false);
  const [voiceScope, setVoiceScope] = useState("all");
  const [voiceMessage, setVoiceMessage] = useState("");

  const audioRef = useRef(null);
  const audioUrlRef = useRef(null);
  const speechQueueRef = useRef([]);
  const queueIndexRef = useRef(0);
  const heartbeatTimerRef = useRef(null);
  const isPlayingRef = useRef(false);
  const activeUtteranceRef = useRef(null);

  // Preload browser voices on mount
  useEffect(() => {
    if (typeof window !== "undefined" && window.speechSynthesis) {
      window.speechSynthesis.getVoices();
      window.speechSynthesis.onvoiceschanged = () => {
        window.speechSynthesis.getVoices();
      };
    }
  }, []);

  // Prevent multiple saves
  const historySavedRef = useRef(false);

  /*
   * 2. SAVE ANALYSIS TO LOCAL HISTORY
   */
  useEffect(() => {
    if (!prediction || historySavedRef.current) return;
    historySavedRef.current = true;

    try {
      const existing = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
      const records = Array.isArray(existing) ? existing : [];

      const recordId = `analysis-${Date.now()}-${prediction.crop}-${prediction.disease}`;
      const record = {
        id: recordId,
        date: new Date().toISOString(),
        timestamp: Date.now(),
        crop: prediction.crop,
        condition: prediction.condition,
        disease: prediction.disease,
        confidence: prediction.confidence,
        severity: rawSeverity?.severity || "None",
        affected_area: rawSeverity?.affected_area || "0%",
        health_score: rawSeverity?.health_score ?? (prediction.condition === "Healthy" ? 100 : null),
        severityDetails: rawSeverity,
        disease_info: rawDiseaseInfo,
        symptoms: rawDiseaseInfo?.symptoms || [],
        fileName: fileName || "leaf-image.jpg",
        image: image || null,
      };

      const updated = [record, ...records].slice(0, 100);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
    } catch (e) {
      console.warn("Failed to save history to localStorage:", e);
    }
  }, [prediction, rawSeverity, rawDiseaseInfo, fileName, image]);

  /*
   * 3. DYNAMIC TRANSLATION ON LANGUAGE CHANGE
   */
  useEffect(() => {
    if (!prediction) return;

    let isCurrent = true;
    const updateLanguage = async () => {
      if (selectedLanguage === "en") {
        setDisplayCrop(prediction.crop);
        setDisplayCondition(prediction.condition);
        setDisplayDisease(prediction.disease);
        setDisplaySeverity(rawSeverity?.severity || "None");
        setDisplaySymptoms(rawDiseaseInfo?.symptoms || []);
        setDisplayCauses(rawDiseaseInfo?.causes || "");
        setDisplayRecommendations(rawDiseaseInfo?.recommendations || []);
        setDisplayPrevention(rawDiseaseInfo?.prevention || []);
        return;
      }

      setTranslating(true);
      try {
        const [
          tCrop,
          tCondition,
          tDisease,
          tSeverity,
          tCauses,
          tSymptoms,
          tRecs,
          tPrev,
        ] = await Promise.all([
          translateText(prediction.crop, selectedLanguage),
          translateText(prediction.condition, selectedLanguage),
          translateText(prediction.disease, selectedLanguage),
          translateText(rawSeverity?.severity || "None", selectedLanguage),
          translateText(rawDiseaseInfo?.causes || "", selectedLanguage),
          translateTexts(rawDiseaseInfo?.symptoms || [], selectedLanguage),
          translateTexts(rawDiseaseInfo?.recommendations || [], selectedLanguage),
          translateTexts(rawDiseaseInfo?.prevention || [], selectedLanguage),
        ]);

        if (isCurrent) {
          setDisplayCrop(tCrop);
          setDisplayCondition(tCondition);
          setDisplayDisease(tDisease);
          setDisplaySeverity(tSeverity);
          setDisplayCauses(tCauses);
          setDisplaySymptoms(tSymptoms);
          setDisplayRecommendations(tRecs);
          setDisplayPrevention(tPrev);
        }
      } catch (err) {
        console.warn("Translation failed gracefully:", err);
      } finally {
        if (isCurrent) setTranslating(false);
      }
    };

    updateLanguage();
    return () => {
      isCurrent = false;
    };
  }, [selectedLanguage, prediction, rawSeverity, rawDiseaseInfo]);

  /*
   * 4. SPEECH SYNTHESIS & FULL NARRATION
   */
  const buildSpeechText = (scope, lang) => {
    const isUnsupported =
      prediction?.unsupported ||
      prediction?.condition === "Unsupported" ||
      prediction?.crop === "Unsupported Image / Crop";
    const isHealthy = prediction?.condition === "Healthy";
    const conf = prediction?.confidence ? Math.round(prediction.confidence) : 0;

    if (isUnsupported) {
      if (lang === "te") {
        return "పంట విశ్లేషణ ఫలితం: మద్దతు లేని చిత్రం లేదా పంట. ఈ చిత్రం మోడల్ గుర్తించగలిగే 14 పంటలలో దేనికీ సరిపోలడం లేదు. దయచేసి స్పష్టమైన పంట ఆకు ఫోటోను అప్‌లోడ్ చేయండి.";
      }
      if (lang === "hi") {
        return "फसल विश्लेषण परिणाम: असमर्थित छवि या फसल। यह चित्र 14 समर्थित फसलों में से किसी से मेल नहीं खाता। कृपया अच्छी रोशनी में फसल की पत्ती की स्पष्ट तस्वीर अपलोड करें।";
      }
      return "Crop diagnosis: Unsupported image or crop. The uploaded image does not match any of the 14 supported crop leaf classes. Please upload a clear photo of a crop leaf in good lighting.";
    }

    if (lang === "te") {
      const parts = [];
      if (scope === "all" || scope === "summary") {
        parts.push(`పంట విశ్లేషణ నివేదిక.`);
        parts.push(`పంట: ${displayCrop}.`);
        parts.push(`పరిస్థితి: ${displayCondition}.`);
        parts.push(`గుర్తించిన వ్యాధి: ${displayDisease}.`);
        if (conf > 0) parts.push(`ఖచ్చితత్వం: ${conf} శాతం.`);
        if (rawSeverity?.severity && rawSeverity.severity !== "N/A") {
          parts.push(`తీవ్రత స్థాయి: ${displaySeverity}. ప్రభావిత ఆకు వైశాల్యం: ${rawSeverity.affected_area || '0 శాతం'}.`);
        }
      }
      if (scope === "all" && isHealthy) {
        parts.push(`ఆకుపై ఎటువంటి వ్యాధి లక్షణాలు కనిపించలేదు.`);
        if (displayRecommendations?.length > 0) {
          parts.push(`సిఫార్సు: ${displayRecommendations.join('. ')}.`);
        }
        if (displayPrevention?.length > 0) {
          parts.push(`నివారణ చర్యలు: ${displayPrevention.join('. ')}.`);
        }
      } else if (scope === "all" || scope === "actions") {
        if (scope === "all") {
          if (displaySymptoms?.length > 0) {
            parts.push(`లక్షణాలు: ${displaySymptoms.join('. ')}.`);
          }
          if (displayCauses) {
            parts.push(`కారణాలు: ${displayCauses}.`);
          }
        }
        if (displayRecommendations?.length > 0) {
          parts.push(`చికిత్స మరియు సిఫార్సులు: ${displayRecommendations.join('. ')}.`);
        }
        if (displayPrevention?.length > 0) {
          parts.push(`నివారణ చర్యలు: ${displayPrevention.join('. ')}.`);
        }
      }
      return parts.join(" ");
    }

    if (lang === "hi") {
      const parts = [];
      if (scope === "all" || scope === "summary") {
        parts.push(`फसल रोग विश्लेषण रिपोर्ट।`);
        parts.push(`फसल: ${displayCrop}।`);
        parts.push(`स्थिति: ${displayCondition}।`);
        parts.push(`पहचानी गई बीमारी: ${displayDisease}।`);
        if (conf > 0) parts.push(`सटीकता: ${conf} प्रतिशत।`);
        if (rawSeverity?.severity && rawSeverity.severity !== "N/A") {
          parts.push(`गंभीरता: ${displaySeverity}। प्रभावित पत्ती क्षेत्र: ${rawSeverity.affected_area || '0 प्रतिशत'}।`);
        }
      }
      if (scope === "all" && isHealthy) {
        parts.push(`पत्ती पर किसी बीमारी के लक्षण नहीं पाए गए।`);
        if (displayRecommendations?.length > 0) {
          parts.push(`सलाह: ${displayRecommendations.join('। ')}।`);
        }
        if (displayPrevention?.length > 0) {
          parts.push(`रोकथाम के उपाय: ${displayPrevention.join('। ')}।`);
        }
      } else if (scope === "all" || scope === "actions") {
        if (scope === "all") {
          if (displaySymptoms?.length > 0) {
            parts.push(`लक्षण: ${displaySymptoms.join('। ')}।`);
          }
          if (displayCauses) {
            parts.push(`कारण: ${displayCauses}।`);
          }
        }
        if (displayRecommendations?.length > 0) {
          parts.push(`उपचार और सलाह: ${displayRecommendations.join('। ')}।`);
        }
        if (displayPrevention?.length > 0) {
          parts.push(`रोकथाम: ${displayPrevention.join('। ')}।`);
        }
      }
      return parts.join(" ");
    }

    // Default: English
    const parts = [];
    if (scope === "all" || scope === "summary") {
      parts.push(`Crop pathology diagnostic report.`);
      parts.push(`Crop: ${displayCrop}.`);
      parts.push(`Condition: ${displayCondition}.`);
      parts.push(`Identified condition: ${displayDisease}.`);
      if (conf > 0) parts.push(`Model confidence: ${conf} percent.`);
      if (rawSeverity?.severity && rawSeverity.severity !== "N/A") {
        parts.push(`Estimated severity level: ${displaySeverity}, with approximately ${rawSeverity.affected_area || '0%'} affected leaf area.`);
        if (rawSeverity.health_score !== null && rawSeverity.health_score !== undefined) {
          parts.push(`Overall plant vigor index is ${rawSeverity.health_score} out of 100.`);
        }
      }
    }
    if (scope === "all" && isHealthy) {
      parts.push(`No disease lesions detected on foliage. Plant appears healthy.`);
      if (displayRecommendations?.length > 0) {
        parts.push(`Recommended maintenance: ${displayRecommendations.join('. ')}.`);
      }
      if (displayPrevention?.length > 0) {
        parts.push(`Preventive practices: ${displayPrevention.join('. ')}.`);
      }
    } else if (scope === "all" || scope === "actions") {
      if (scope === "all") {
        if (displaySymptoms?.length > 0) {
          parts.push(`Observed symptoms: ${displaySymptoms.join('. ')}.`);
        }
        if (displayCauses) {
          parts.push(`Underlying causes: ${displayCauses}.`);
        }
      }
      if (displayRecommendations?.length > 0) {
        parts.push(`Treatment recommendations: ${displayRecommendations.join('. ')}.`);
      }
      if (displayPrevention?.length > 0) {
        parts.push(`Preventive measures: ${displayPrevention.join('. ')}.`);
      }
    }
    return parts.join(" ");
  };

  const stopVoice = () => {
    if (heartbeatTimerRef.current) {
      clearInterval(heartbeatTimerRef.current);
      heartbeatTimerRef.current = null;
    }
    if (audioRef.current) {
      try {
        audioRef.current.pause();
        audioRef.current.currentTime = 0;
      } catch (e) {
        // Ignore
      }
      audioRef.current = null;
    }
    if (typeof window !== "undefined" && window.speechSynthesis) {
      try {
        window.speechSynthesis.cancel();
      } catch (e) {
        // Ignore
      }
    }
    if (audioUrlRef.current) {
      try {
        URL.revokeObjectURL(audioUrlRef.current);
      } catch (e) {
        // Ignore
      }
      audioUrlRef.current = null;
    }
    activeUtteranceRef.current = null;
    speechQueueRef.current = [];
    queueIndexRef.current = 0;
    isPlayingRef.current = false;

    setIsSpeaking(false);
    setIsPaused(false);
    setIsLoadingVoice(false);
    setVoiceMessage("");
  };

  const getBrowserVoice = (lang) => {
    if (typeof window === "undefined" || !window.speechSynthesis) return null;
    const voices = window.speechSynthesis.getVoices() || [];
    if (!voices.length) return null;

    if (lang === "hi") {
      const hi = voices.find(
        (v) => v.lang === "hi-IN" || v.lang.startsWith("hi") || v.name.toLowerCase().includes("hindi")
      );
      if (hi) return hi;
    } else if (lang === "te") {
      const te = voices.find(
        (v) => v.lang === "te-IN" || v.lang.startsWith("te") || v.name.toLowerCase().includes("telugu")
      );
      if (te) return te;
    } else {
      const en = voices.find(
        (v) => (v.lang === "en-US" || v.lang === "en-GB" || v.lang.startsWith("en"))
      );
      if (en) return en;
    }
    return voices[0];
  };

  const splitTextIntoChunks = (text) => {
    if (!text) return [];
    // Split on sentence-ending punctuation (. ? ! । newline)
    const rawSentences = text
      .split(/(?<=[.?!।\n])\s+/)
      .map((s) => s.trim())
      .filter((s) => s.length > 0);

    const safeChunks = [];
    for (const sent of rawSentences) {
      if (sent.length <= 160) {
        safeChunks.push(sent);
      } else {
        // Sub-chunk long sentence by comma/semicolon/space to stay under utterance limits
        const words = sent.split(" ");
        let buf = "";
        for (const w of words) {
          if ((buf + " " + w).trim().length > 140) {
            if (buf) safeChunks.push(buf.trim());
            buf = w;
          } else {
            buf = buf ? `${buf} ${w}` : w;
          }
        }
        if (buf.trim()) safeChunks.push(buf.trim());
      }
    }
    return safeChunks.length > 0 ? safeChunks : [text];
  };

  const startBrowserKeepalive = () => {
    if (heartbeatTimerRef.current) clearInterval(heartbeatTimerRef.current);
    // Chrome bug workaround: pause/resume every 9s keeps speech engine active
    heartbeatTimerRef.current = setInterval(() => {
      if (typeof window !== "undefined" && window.speechSynthesis && window.speechSynthesis.speaking && !window.speechSynthesis.paused) {
        window.speechSynthesis.pause();
        window.speechSynthesis.resume();
      }
    }, 9000);
  };

  const playBrowserChunk = (index, lang) => {
    if (!isPlayingRef.current) return;
    const queue = speechQueueRef.current;
    if (index >= queue.length) {
      stopVoice();
      setVoiceMessage(lang === "hi" ? "वाचन पूरा हुआ।" : lang === "te" ? "ప్లేబ్యాక్ పూర్తయింది." : "Playback completed.");
      return;
    }

    queueIndexRef.current = index;
    const textChunk = queue[index];
    const utterance = new SpeechSynthesisUtterance(textChunk);
    activeUtteranceRef.current = utterance; // Prevent GC in Chrome

    utterance.lang = lang === "te" ? "te-IN" : lang === "hi" ? "hi-IN" : "en-US";
    utterance.rate = 0.95;
    utterance.pitch = 1.0;

    const voice = getBrowserVoice(lang);
    if (voice) {
      utterance.voice = voice;
    }

    utterance.onend = () => {
      activeUtteranceRef.current = null;
      if (isPlayingRef.current) {
        playBrowserChunk(index + 1, lang);
      }
    };

    utterance.onerror = (e) => {
      console.warn("Speech chunk error:", e);
      activeUtteranceRef.current = null;
      if (isPlayingRef.current) {
        playBrowserChunk(index + 1, lang);
      }
    };

    try {
      window.speechSynthesis.speak(utterance);
    } catch (err) {
      console.warn("Speak error:", err);
      stopVoice();
    }
  };

  const fallbackBrowserSpeak = (text, lang) => {
    if (typeof window === "undefined" || !window.speechSynthesis) {
      setIsLoadingVoice(false);
      setIsSpeaking(false);
      setIsPaused(false);
      setVoiceMessage("Audio playback not supported in this browser.");
      return;
    }

    window.speechSynthesis.cancel();
    const chunks = splitTextIntoChunks(text);
    if (chunks.length === 0) {
      setIsLoadingVoice(false);
      return;
    }

    speechQueueRef.current = chunks;
    queueIndexRef.current = 0;
    isPlayingRef.current = true;

    setIsLoadingVoice(false);
    setIsSpeaking(true);
    setIsPaused(false);
    setVoiceMessage(lang === "hi" ? "आवाज सुनाई जा रही है..." : "Playing voice narration...");

    startBrowserKeepalive();
    playBrowserChunk(0, lang);
  };

  const handleSpeak = async () => {
    stopVoice();
    setIsLoadingVoice(true);
    setVoiceMessage(
      selectedLanguage === "hi"
        ? "ऑडियो तैयार किया जा रहा है..."
        : "Synthesizing voice response..."
    );

    const textToSpeak = buildSpeechText(voiceScope, selectedLanguage);

    try {
      const audioBlob = await generateSpeech(textToSpeak, selectedLanguage);
      const audioUrl = URL.createObjectURL(audioBlob);
      audioUrlRef.current = audioUrl;

      const audio = new Audio(audioUrl);
      audioRef.current = audio;

      audio.onplay = () => {
        setIsSpeaking(true);
        setIsPaused(false);
        setVoiceMessage(selectedLanguage === "hi" ? "आवाज सुनाई जा रही है..." : "Playing voice narration...");
      };

      audio.onpause = () => {
        if (!audio.ended && isPlayingRef.current) {
          setIsPaused(true);
          setVoiceMessage(selectedLanguage === "hi" ? "रोक दिया गया।" : "Paused.");
        }
      };

      audio.onended = () => {
        stopVoice();
        setVoiceMessage(selectedLanguage === "hi" ? "वाचन पूरा हुआ।" : "Playback completed.");
      };

      audio.onerror = (e) => {
        console.warn("Audio element playback error, falling back to Web Speech API:", e);
        stopVoice();
        fallbackBrowserSpeak(textToSpeak, selectedLanguage);
      };

      setIsLoadingVoice(false);
      setIsSpeaking(true);
      setIsPaused(false);
      isPlayingRef.current = true;
      await audio.play();
    } catch (err) {
      console.warn("Backend TTS failed, falling back to Web Speech API:", err);
      fallbackBrowserSpeak(textToSpeak, selectedLanguage);
    }
  };

  const handlePause = () => {
    if (audioRef.current && !audioRef.current.paused) {
      try {
        audioRef.current.pause();
      } catch (e) {
        // Ignore
      }
      setIsPaused(true);
      setVoiceMessage(selectedLanguage === "hi" ? "रोक दिया गया।" : "Paused.");
    } else if (typeof window !== "undefined" && window.speechSynthesis && window.speechSynthesis.speaking) {
      try {
        window.speechSynthesis.pause();
      } catch (e) {
        // Ignore
      }
      setIsPaused(true);
      setVoiceMessage(selectedLanguage === "hi" ? "रोक दिया गया।" : "Paused.");
    }
  };

  const handleResume = async () => {
    if (audioRef.current && isPaused) {
      try {
        await audioRef.current.play();
        setIsPaused(false);
        setVoiceMessage(selectedLanguage === "hi" ? "आवाज सुनाई जा रही है..." : "Playing voice narration...");
      } catch (err) {
        console.warn("Failed to resume audio element:", err);
      }
    } else if (typeof window !== "undefined" && window.speechSynthesis && window.speechSynthesis.paused) {
      try {
        window.speechSynthesis.resume();
        setIsPaused(false);
        setVoiceMessage(selectedLanguage === "hi" ? "आवाज सुनाई जा रही है..." : "Playing voice narration...");
      } catch (err) {
        console.warn("Failed to resume speech synthesis:", err);
      }
    }
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopVoice();
    };
  }, []);

  if (!prediction) {
    return (
      <div className="result-page">
        <div className="result-container">
          <div className="result-card empty-result" style={{ textAlign: "center", padding: "40px" }}>
            <div style={{ fontSize: "48px" }}>🌱</div>
            <h2>No Analysis Data Found</h2>
            <p style={{ color: "#666" }}>Please upload or take a photo of a crop leaf first.</p>
            <button className="primary-button" onClick={() => navigate("/analyze")}>
              Analyze Leaf
            </button>
          </div>
        </div>
      </div>
    );
  }

  const isHealthy = prediction.condition === "Healthy";
  const isUnknown = prediction.condition === "Unknown" || prediction.unsupported;
  const isDiseased = !isHealthy && !isUnknown;

  return (
    <div className="result-page">
      <div className="result-container">
        {/* HEADER & LANGUAGE SWITCHER */}
        <div className="result-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "16px" }}>
          <div>
            <h1>🌿 {t("title")}</h1>
            <p>{t("subtitle")}</p>
          </div>

          {/* Multilingual Selector */}
          <div style={{ display: "flex", alignItems: "center", gap: "8px", background: "#f0fdf4", padding: "8px 14px", borderRadius: "10px", border: "1px solid #ccebd7" }}>
            <label htmlFor="lang-select" style={{ fontWeight: 600, fontSize: "0.9rem", color: "#166534" }}>🌐 {t("language")}:</label>
            <select
              id="lang-select"
              value={selectedLanguage}
              onChange={(e) => setSelectedLanguage(e.target.value)}
              style={{
                padding: "6px 12px",
                borderRadius: "6px",
                border: "1px solid #a7d7b9",
                background: "#ffffff",
                fontWeight: 600,
                color: "#1b382b",
                cursor: "pointer"
              }}
            >
              <option value="en">English</option>
              <option value="te">తెలుగు (Telugu)</option>
              <option value="hi">हिन्दी (Hindi)</option>
            </select>
          </div>
        </div>

        {translating && (
          <div style={{ padding: "8px", background: "#fef3c7", borderRadius: "6px", color: "#92400e", fontSize: "0.85rem", marginBottom: "12px" }}>
            {selectedLanguage === "te"
              ? "ఫలితాలను తెలుగులోకి అనువదిస్తోంది..."
              : "परिणामों का हिंदी में अनुवाद किया जा रहा है..."}
          </div>
        )}

        {/* IMAGE PREVIEW */}
        {image && (
          <div className="result-image-card">
            <img src={image} alt="Analyzed leaf" className="result-image" />
            {fileName && <p className="result-file-name">📄 {fileName}</p>}
          </div>
        )}

        {/* PRIMARY METRICS CARD */}
        <div className="result-card">
          <div className="result-info-grid">
            <div className="info-box">
              <span className="info-icon">🌱</span>
              <span className="info-label">{t("crop")}</span>
              <strong>{displayCrop}</strong>
            </div>

            <div className="info-box">
              <span className="info-icon">🌿</span>
              <span className="info-label">{t("condition")}</span>
              <strong style={{
                color: isHealthy ? "#2e7d32" : isUnknown ? "#f57c00" : "#d32f2f"
              }}>
                {displayCondition}
              </strong>
            </div>

            <div className="info-box">
              <span className="info-icon">🦠</span>
              <span className="info-label">{t("diseaseIdentified")}</span>
              <strong>{displayDisease}</strong>
            </div>

            <div className="info-box" title="Model confidence represents the probability/strength assigned to the predicted class among all trained classes. It is not a measurement of disease severity or affected area.">
              <span className="info-icon">🎯</span>
              <span className="info-label">{t("confidence")}</span>
              <strong>
                {prediction.confidence ? `${Number(prediction.confidence).toFixed(2)}%` : "N/A"}
              </strong>
              <small style={{ color: "#777", marginTop: "2px", fontSize: "0.75rem" }}>
                {t("classProbability")}
              </small>
            </div>
          </div>

          {/* SEVERITY & HEALTH SCORE (Decoupled from confidence) */}
          <div style={{
            marginTop: "20px",
            paddingTop: "20px",
            borderTop: "1px solid #eef2f0",
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
            gap: "16px"
          }}>
            <div className="info-box" style={{ background: "#fbfcfc" }}>
              <span className="info-icon">⚠️</span>
              <span className="info-label">{t("severityLevel")}</span>
              <strong>
                {isUnknown
                  ? "N/A"
                  : isHealthy
                  ? t("none")
                  : (displaySeverity && displaySeverity !== "N/A" ? displaySeverity : t("notAvailable"))}
              </strong>
              <small style={{ color: "#777", marginTop: "2px" }}>
                {isUnknown
                  ? t("unsupportedImage")
                  : isHealthy
                  ? t("healthyFoliage")
                  : rawSeverity?.is_estimated
                  ? t("estimatedLesion")
                  : t("directAssessment")}
              </small>
            </div>

            <div className="info-box" style={{ background: "#fbfcfc" }}>
              <span className="info-icon">📐</span>
              <span className="info-label">{t("affectedArea")}</span>
              <strong>
                {isUnknown
                  ? "N/A"
                  : isHealthy
                  ? "0%"
                  : (rawSeverity?.affected_area && rawSeverity.affected_area !== "N/A" && rawSeverity.affected_area !== "Unable to determine"
                    ? rawSeverity.affected_area
                    : t("notAvailableModel"))}
              </strong>
              <small style={{ color: "#777", marginTop: "2px" }}>
                {isUnknown ? t("unsupportedImage") : isHealthy ? t("noLesions") : t("surfaceLesionRatio")}
              </small>
            </div>

            <div className="info-box" style={{ background: "#fbfcfc" }}>
              <span className="info-icon">💚</span>
              <span className="info-label">{t("healthScore")}</span>
              <strong style={{
                color: isUnknown
                  ? "#777"
                  : (rawSeverity?.health_score ?? (isHealthy ? 100 : 50)) >= 80
                  ? "#2e7d32"
                  : "#c62828"
              }}>
                {isUnknown
                  ? "N/A"
                  : isHealthy
                  ? "100 / 100"
                  : rawSeverity?.health_score !== null && rawSeverity?.health_score !== undefined
                  ? `${rawSeverity.health_score} / 100`
                  : t("notAvailable")}
              </strong>
              <small style={{ color: "#777", marginTop: "2px" }}>
                {isUnknown ? t("unsupportedImage") : t("vigorIndex")}
              </small>
            </div>
          </div>

          {/* Honest estimation disclaimer */}
          {!isUnknown && rawSeverity?.method && rawSeverity.method !== "N/A" && (
            <p style={{ margin: "14px 0 0 0", fontSize: "0.8rem", color: "#666", textAlign: "right" }}>
              {t("diagnosticModel")} <em>{rawSeverity.method}</em>
            </p>
          )}
        </div>

        {/* VOICE ASSISTANT CARD */}
        <div className="voice-card">
          <div className="voice-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
              <div className="voice-icon" style={{ fontSize: "28px" }}>🔊</div>
              <div>
                <h2 style={{ margin: 0, fontSize: "1.2rem", color: "#166534" }}>{t("voiceAssistant")}</h2>
                <p style={{ margin: "2px 0 0 0", fontSize: "0.85rem", color: "#666" }}>
                  {t("voiceSubtitle")}
                </p>
              </div>
            </div>

            {/* Reading Mode Selector */}
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <label htmlFor="voice-scope-select" style={{ fontSize: "0.85rem", fontWeight: 600, color: "#166534" }}>
                {t("readingScope")}
              </label>
              <select
                id="voice-scope-select"
                value={voiceScope}
                onChange={(e) => {
                  stopVoice();
                  setVoiceScope(e.target.value);
                }}
                disabled={isSpeaking || isLoadingVoice}
                style={{
                  padding: "6px 10px",
                  borderRadius: "6px",
                  border: "1px solid #ccebd7",
                  background: "#ffffff",
                  fontSize: "0.85rem",
                  fontWeight: 600,
                  color: "#1b382b",
                  cursor: isSpeaking ? "not-allowed" : "pointer"
                }}
              >
                <option value="all">{t("fullReport")}</option>
                <option value="summary">{t("summaryOnly")}</option>
                <option value="actions">{t("actionsOnly")}</option>
              </select>
            </div>
          </div>

          <div className="voice-controls" style={{ display: "flex", gap: "10px", alignItems: "center", marginTop: "16px", flexWrap: "wrap" }}>
            {/* Play / Resume */}
            {!isSpeaking ? (
              <button
                type="button"
                className="voice-speak-button"
                onClick={handleSpeak}
                disabled={isLoadingVoice}
                style={{ display: "inline-flex", alignItems: "center", gap: "6px" }}
              >
                {isLoadingVoice ? t("synthesizingAudio") : t("readAloud")}
              </button>
            ) : isPaused ? (
              <button
                type="button"
                className="voice-speak-button"
                onClick={handleResume}
                style={{ display: "inline-flex", alignItems: "center", gap: "6px", background: "#16a34a" }}
              >
                {t("resume")}
              </button>
            ) : (
              <button
                type="button"
                className="voice-pause-button"
                onClick={handlePause}
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "6px",
                  padding: "8px 16px",
                  borderRadius: "8px",
                  border: "none",
                  background: "#f59e0b",
                  color: "#ffffff",
                  fontWeight: 600,
                  cursor: "pointer"
                }}
              >
                {t("pause")}
              </button>
            )}

            {/* Stop button */}
            {(isSpeaking || isPaused || isLoadingVoice) && (
              <button
                type="button"
                className="voice-stop-button"
                onClick={stopVoice}
                style={{ display: "inline-flex", alignItems: "center", gap: "6px" }}
              >
                {t("stop")}
              </button>
            )}

            {voiceMessage && (
              <span style={{ fontSize: "0.85rem", color: "#374151", fontWeight: 500, paddingLeft: "8px", fontStyle: "italic" }}>
                {voiceMessage}
              </span>
            )}
          </div>
        </div>

        {/* FOR UNSUPPORTED IMAGES: Show dedicated guidance instead of disease info */}
        {isUnknown ? (
          <div className="result-card" style={{ borderLeft: "4px solid #f59e0b" }}>
            <div className="section-title">
              <span>⚠️</span>
              <h2>{t("unsupportedTitle")}</h2>
            </div>
            <p style={{ lineHeight: 1.6, color: "#4b5563", marginBottom: "12px" }}>
              {t("unsupportedDesc")}
            </p>
            <div style={{ background: "#fffbeb", padding: "14px 18px", borderRadius: "10px", border: "1px solid #fef3c7" }}>
              <strong style={{ color: "#92400e", display: "block", marginBottom: "6px" }}>{t("guidanceHeading")}</strong>
              <ul style={{ margin: 0, paddingLeft: "20px", color: "#78350f", lineHeight: 1.6 }}>
                <li>{t("guidance1")}</li>
                <li>{t("guidance2")}</li>
                <li>{t("guidance3")}</li>
              </ul>
            </div>
          </div>
        ) : (
          <>
            {/* SYMPTOMS & CLINICAL OBSERVATIONS */}
            <div className="result-card">
              <div className="section-title">
                <span>👀</span>
                <h2>{isHealthy ? t("leafHealthObs") : t("symptomsTitle")}</h2>
              </div>
              {Array.isArray(displaySymptoms) && displaySymptoms.length > 0 ? (
                <ul className="simple-list">
                  {displaySymptoms.map((s, idx) => (
                    <li key={idx}>{s}</li>
                  ))}
                </ul>
              ) : (
                <p style={{ color: "#666" }}>
                  {isHealthy
                    ? t("healthySymptomsText")
                    : t("noSymptomsText")}
                </p>
              )}
            </div>

            {/* CAUSES */}
            {displayCauses && (
              <div className="result-card">
                <div className="section-title">
                  <span>❓</span>
                  <h2>{isHealthy ? t("cropHealthAssessment") : t("causesTitle")}</h2>
                </div>
                <p style={{ lineHeight: 1.6, color: "#333", margin: 0 }}>
                  {displayCauses}
                </p>
              </div>
            )}

            {/* RECOMMENDATIONS */}
            {Array.isArray(displayRecommendations) && displayRecommendations.length > 0 && (
              <div className="result-card">
                <div className="section-title">
                  <span>💡</span>
                  <h2>{isHealthy ? t("recommendedCare") : t("recommendationsTitle")}</h2>
                </div>
                <ul className="simple-list action-list">
                  {displayRecommendations.map((r, idx) => (
                    <li key={idx}>{r}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* PREVENTION TIPS */}
            {Array.isArray(displayPrevention) && displayPrevention.length > 0 && (
              <div className="result-card">
                <div className="section-title">
                  <span>🛡️</span>
                  <h2>{isHealthy ? t("preventivePractices") : t("preventionTitle")}</h2>
                </div>
                <ul className="simple-list action-list">
                  {displayPrevention.map((p, idx) => (
                    <li key={idx}>{p}</li>
                  ))}
                </ul>
              </div>
            )}
          </>
        )}



        {/* ACTIONS & NAVIGATION */}
        <div className="result-actions" style={{ display: "flex", gap: "12px", justifyContent: "center", flexWrap: "wrap", marginTop: "24px" }}>
          <button className="primary-button" onClick={() => navigate("/analyze")}>
            {t("analyzeAnother")}
          </button>
          <button className="dashboard-button" onClick={() => navigate("/dashboard")}>
            {t("viewDashboard")}
          </button>
          <button className="history-button" onClick={() => navigate("/history")}>
            {t("viewHistory")}
          </button>
          <button className="secondary-button" onClick={() => navigate("/")}>
            {t("backHome")}
          </button>
        </div>
      </div>
    </div>
  );
}

export default Result;