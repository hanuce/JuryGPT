# backend/voice_recognition.py

import speech_recognition as sr
import tensorflow as tf

class VoiceRecognition:
    def __init__(self, model_path):
        # Teachable Machine modelini yükleyelim
        self.model = tf.keras.models.load_model(model_path)
        self.recognizer = sr.Recognizer()

    def listen_for_audio(self):
        with sr.Microphone() as source:
            print("Listening...")
            audio = self.recognizer.listen(source)
        
        try:
            # Audioyu metne dönüştürelim
            text = self.recognizer.recognize_google(audio)
            print(f"Recognized Text: {text}")
            return text
        except sr.UnknownValueError:
            print("Could not understand the audio")
            return None
        except sr.RequestError:
            print("Could not request results; check your network connection")
            return None

    def predict_class(self, audio_data):
        # Modelimizle sesin sınıfını tahmin etme işlemi
        predictions = self.model.predict(audio_data)
        predicted_class = predictions.argmax(axis=-1)
        return predicted_class
