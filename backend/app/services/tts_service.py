from pathlib import Path
from piper import PiperVoice
import wave
import io


BASE_DIR = Path(__file__).resolve().parents[2]
VOICE_DIR = BASE_DIR / "voices"


VOICE_MODELS = {
    "en": VOICE_DIR / "en_US-lessac-medium.onnx",
    "te": VOICE_DIR / "te_IN-venkatesh-medium.onnx",
    "hi": VOICE_DIR / "hi_IN-priyamvada-medium.onnx",
}


class TTSService:
    def __init__(self):
        self.voices = {}

    def get_voice(self, language: str) -> PiperVoice:
        if language not in VOICE_MODELS:
            raise ValueError("Unsupported language")

        if language not in self.voices:
            model_path = VOICE_MODELS[language]

            if not model_path.exists():
                raise FileNotFoundError(
                    f"Voice model not found: {model_path}"
                )

            self.voices[language] = PiperVoice.load(str(model_path))

        return self.voices[language]

    def synthesize(self, text: str, language: str) -> bytes:
        voice = self.get_voice(language)
        cleaned_text = " ".join(text.split()).strip()

        output = io.BytesIO()

        with wave.open(output, "wb") as wav_file:
            voice.synthesize_wav(cleaned_text, wav_file)

        return output.getvalue()


tts_service = TTSService()
