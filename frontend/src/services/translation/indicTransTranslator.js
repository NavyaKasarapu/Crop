import { pipeline, env } from "@huggingface/transformers";

const MODEL_ID =
  "hari31416/indictrans2-en-indic-dist-200M-ONNX-int8";

env.allowLocalModels = false;
env.useBrowserCache = true;

let translatorPromise = null;

const LANGUAGE_CODES = {
  hi: "hin_Deva",
  te: "tel_Telu",
};

async function loadTranslator() {
  if (!translatorPromise) {
    translatorPromise = pipeline(
      "translation",
      MODEL_ID,
      {
        device: "wasm",
      }
    );
  }

  return translatorPromise;
}

export async function translateText(text, language) {
  const cleanText = String(text || "").trim();

  if (!cleanText) {
    return "";
  }

  if (language === "en") {
    return cleanText;
  }

  const targetLanguage = LANGUAGE_CODES[language];

  if (!targetLanguage) {
    throw new Error(
      "Unsupported translation language."
    );
  }

  const translator =
    await loadTranslator();

  const result = await translator(
    cleanText,
    {
      src_lang: "eng_Latn",
      tgt_lang: targetLanguage,
    }
  );

  if (
    Array.isArray(result) &&
    result[0]?.translation_text
  ) {
    return result[0].translation_text;
  }

  throw new Error(
    "Translation returned an unexpected result."
  );
}