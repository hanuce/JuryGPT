import librosa
import numpy as np
import pickle
import os
from sklearn.svm import SVC

# Ses dosyasından özellik çıkarımı
def extract_audio_features(audio_file):
    y, sr = librosa.load(audio_file)
    mfccs = librosa.feature.mfcc(y=y, sr=sr)
    return np.mean(mfccs.T, axis=0)

# Model eğitimi
def train_voice_model():
    X = []  # Özellikler
    y = []  # Etiketler

    # 'data/' klasöründeki tüm ses dosyalarını işleyin
    for filename in os.listdir("data/"):
        if filename.endswith(".wav"):
            label = int(filename.split('_')[1].split('.')[0])  # Person1, Person2...
            audio_features = extract_audio_features(f"data/{filename}")
            X.append(audio_features)
            y.append(label)

    X = np.array(X)
    y = np.array(y)

    # Destek vektör makinasi (SVM) ile model eğitimi
    model = SVC(kernel='linear')
    model.fit(X, y)

    # Modeli kaydedin
    with open('voice_recognition_model.pkl', 'wb') as f:
        pickle.dump(model, f)

if __name__ == "__main__":
    train_voice_model()
