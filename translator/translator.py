
import os
import sounddevice as sd
import scipy.io.wavfile as wavfile
import whisper
from gtts import gTTS
from pydub import AudioSegment
import google.generativeai as genai
import streamlit as st
import tempfile
import base64

class SpeechTranslation:
    def init(self, sample_rate=16000, record_time=10):
        self.sample_rate = sample_rate
        self.record_time = record_time
        self.input_path = "./input_audio.wav"
        self.output_path = "./output_audio.wav"
        self.whisper_model = whisper.load_model("base")
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY", ""))
        self.gemini_model = genai.GenerativeModel("gemini-2.0-flash")

    def record(self):
        recording = sd.rec(int(self.sample_rate * self.record_time),
                           samplerate=self.sample_rate,
                           channels=1, dtype='int16')
        sd.wait()
        wavfile.write(self.input_path, rate=self.sample_rate, data=recording)

    def transcribe(self):
        result = self.whisper_model.transcribe(self.input_path)
        return result['text']

    def translate(self, text):
        response = self.gemini_model.generate_content(f"Translate this to English:\n{text}")
        return response.text.strip()

    def speak(self, text):
        tts = gTTS(text, lang='en')
        tts.save(self.output_path)
        AudioSegment.from_file(self.output_path).export(self.output_path, format="wav")

    def get_audio_base64(self):
        with open(self.output_path, 'rb') as f:
            audio_bytes = f.read()
        return base64.b64encode(audio_bytes).decode()

    def clean_up(self):
        if os.path.exists(self.input_path):
            os.remove(self.input_path)
        if os.path.exists(self.output_path):
            os.remove(self.output_path)

def main():
    st.title("🎙 Speech Translator")
    st.markdown("Record your speech in any language and translate it to English with audio output!")

    duration = st.slider("Recording Duration (seconds)", 3, 20, 10)
    translator = SpeechTranslation(record_time=duration)

    if st.button("🔴 Start Recording"):
        with st.spinner("Recording audio..."):
            translator.record()
        st.success("Recording complete!")

        with st.spinner("Transcribing..."):
            transcription = translator.transcribe()
        st.write("📝 Transcription:", transcription)

        with st.spinner("Translating..."):
            translated = translator.translate(transcription)
        st.write("🌍 Translation (English):", translated)

        with st.spinner("Generating speech..."):
            translator.speak(translated)
            audio_base64 = translator.get_audio_base64()
            audio_html = f"""
                <audio controls autoplay>
                <source src="data:audio/wav;base64,{audio_base64}" type="audio/wav">
                </audio>
            """
            st.markdown(audio_html, unsafe_allow_html=True)

        translator.clean_up()

if name == "main":
    main()
