from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import Screen
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.screenmanager import ScreenManager
import os
from threading import Thread
import sounddevice as sd
from scipy.io.wavfile import write
import numpy as np
import soundfile as sf  # Ses dosyalarını okuma için
import librosa  # Ses dosyalarını işlemek için
import tensorflow as tf  # Model eğitimi için
from sklearn.preprocessing import LabelEncoder
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from sklearn.preprocessing import LabelEncoder
import librosa
import sqlite3


# Veritabanı bağlantısı
def get_db_connection():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    conn = sqlite3.connect('../data/database.db')  # Veritabanı dosyasına bağlanıyoruz
    conn.row_factory = sqlite3.Row  # Sütun isimlerine dictionary tarzında erişebilmek için row_factory ayarını yapıyoruz
    return conn


class SpeechClassificationScreen(Screen):
    def __init__(self, **kwargs):
        super(SpeechClassificationScreen, self).__init__(**kwargs)

        # Ana düzen
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Başlık
        self.layout.add_widget(Label(text="Debater Speech Training", size_hint_y=None, height=60, font_size=30, bold=True))

        # Okunacak İngilizce metin
        text_part1 = "Please read this text clearly:"
        text_part2 = "The quick brown fox jumps over the lazy dog."
        text_part3 = "Be sure to check the zippers and pockets."
        text_part4 = "A large zebra eagerly walked across the quiet road."

        self.reading_text_label1 = Label(
            text=text_part1,
            bold=True,
            font_size=20,
            color=(1, 1, 1, 1),
            size_hint_y=None,
            height=60,
            halign="center",
            valign="middle"
        )
        self.reading_text_label2 = Label(
            text=f"{text_part2}\n{text_part3}\n{text_part4}",
            bold=True,
            font_size=20,
            color=(1, 1, 0, 1),
            size_hint_y=None,
            height=60,
            halign="center",
            valign="middle"
        )
        self.layout.add_widget(self.reading_text_label1)
        self.layout.add_widget(self.reading_text_label2)

        # Katılımcılar listesi
        self.participants_scroll = ScrollView(size_hint=(1, 1))
        self.participants_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10)
        self.participants_box.bind(minimum_height=self.participants_box.setter('height'))
        self.participants_scroll.add_widget(self.participants_box)
        self.layout.add_widget(self.participants_scroll)

        # Navigasyon butonları
        self.nav_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)
        self.back_button = Button(
            text="Back",
            size_hint=(0.5, 1),
            background_color=(1, 0, 0, 1)  # Kırmızı renk
        )
        self.back_button.bind(on_press=self.go_back)

        self.next_button = Button(
            text="Next",
            size_hint=(0.5, 1),
            background_color=(0, 1, 0, 1)  # Yeşil renk
        )
        self.nav_layout.add_widget(self.back_button)
        self.nav_layout.add_widget(self.next_button)
        self.layout.add_widget(self.nav_layout)

        # Ana düzeni ekrana ekle
        self.add_widget(self.layout)

        # Değişkenler
        self.debate_id = None
        self.participant_count = 0
        self.participant_rows = []

        self.fs = 44100  # Ses örnekleme frekansı (44.1 kHz)
        self.recording = None  # Kaydedilen sesin tutulduğu numpy array
        self.is_recording = False  # Kayıt durumunu kontrol etmek için

    def go_back(self, instance):
        """Back butonuna basıldığında BasicsScreen'e dön."""
        self.manager.current = "basics_screen"

    def setup_screen(self, debate_id):
        """Ekranı verilen debate_id'ye göre hazırlar."""
        self.debate_id = debate_id  # Debate ID'yi kaydet
        print(f"Setting up screen for debate ID: {debate_id}")
        self.fetch_debate_details()  # Veritabanından detayları çek

    def fetch_debate_details(self):
        """Debate detaylarını veritabanından çeker ve ekrana yansıtır."""
        try:
            # Veritabanına bağlantı kur
            connection = get_db_connection()
            cursor = connection.cursor()

            # Debate bilgilerini çek: debate_size ve katılımcılar
            cursor.execute("SELECT debate_size FROM debates WHERE debate_id=?", (self.debate_id,))
            debate_size_result = cursor.fetchone()

            if debate_size_result:
                self.participant_count = debate_size_result["debate_size"]  # Debate size
                print(f"Fetched debate size: {self.participant_count}")
            else:
                print(f"Debate with ID {self.debate_id} not found.")
                self.participant_count = 0

            # Katılımcı isimlerini al
            cursor.execute("SELECT debater_name FROM debaters WHERE debate_id=?", (self.debate_id,))
            participants_result = cursor.fetchall()
            self.participant_names = [row["debater_name"] for row in participants_result]


            connection.close()

            # Katılımcıları ekrana aktar
            self.populate_participants()

        except sqlite3.Error as e:
            print(f"Error fetching debate details: {e}")
            self.participant_count = 0
            self.participant_names = []
            self.populate_participants()


    def populate_participants(self):
        """Katılımcı listesi ve butonları oluşturur."""
        self.participants_box.clear_widgets()  # Mevcut widget'ları temizle
        self.participant_rows = []

        # Katılımcıları listele
        for i in range(self.participant_count):
            if i < len(self.participant_names):  # Katılımcı adı varsa
                participant_name = self.participant_names[i]
            else:  # Katılımcı adı yoksa varsayılan ad ata
                participant_name = f"Person {i + 1}"

            row = self.create_participant_row(participant_name)
            self.participants_box.add_widget(row["layout"])
            self.participant_rows.append(row)


    def create_participant_row(self, participant_name):
        """Katılımcı için bir satır düzeni oluşturur."""
        participant_label = Label(
            text=participant_name,
            size_hint=(0.2, None),
            height=40,
            color=(1, 0, 0, 1)
        )

        # "Change Name" butonu
        change_name_button = Button(
            text="Change Name",
            size_hint=(0.2, None),
            height=40,
            background_color=(0, 0, 1, 1)  # Mavi renk
        )
        change_name_button.bind(on_press=lambda btn: self.change_name_popup(participant_label))

        # "Start Recording" butonu
        start_button = Button(
            text="Start Recording",
            size_hint=(0.2, None),
            height=40,
            background_color=(1, 0, 0, 1)  # Kırmızı renk
        )
        start_button.bind(on_press=lambda btn: self.handle_recording(btn, participant_label.text))

        # "Train Model" butonu
        train_button = Button(
            text="Train Model",
            size_hint=(0.2, None),
            height=40,
            background_color=(0.5, 0.5, 0.5, 1),  # Gri renk (inaktif)
            disabled=True  # Başlangıçta inaktif
        )
        train_button.bind(on_press=lambda btn: self.train_model(btn, participant_label.text))

        # "Status" label
        status_label = Label(
            text="NaN",
            size_hint=(0.2, None),
            height=40,
            color=(1, 0.5, 0, 1)  # Turuncu renk
        )

        # Satır düzeni
        row_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)
        row_layout.add_widget(participant_label)
        row_layout.add_widget(change_name_button)
        row_layout.add_widget(start_button)
        row_layout.add_widget(train_button)
        row_layout.add_widget(status_label)

        return {
            "layout": row_layout,
            "label": participant_label,
            "start_button": start_button,
            "train_button": train_button,
            "status_label": status_label
        }

    def change_name_popup(self, participant_label):
        """Change Name popup oluşturur."""
        popup_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        input_box = TextInput(text=participant_label.text, multiline=False)
        save_button = Button(text="Save", size_hint=(1, 0.2))

        def save_name(instance):
            new_name = input_box.text
            participant_label.text = new_name
            popup.dismiss()

        save_button.bind(on_press=save_name)
        popup_layout.add_widget(input_box)
        popup_layout.add_widget(save_button)

        popup = Popup(title="Change Name", content=popup_layout, size_hint=(0.6, 0.4))
        popup.open()

    def handle_recording(self, button, participant_name):
        """Kayıt işlemini başlatır veya tamamlar."""
        for i, row in enumerate(self.participant_rows):
            if row["label"].text == participant_name:
                if button.text == "Start Recording":
                    button.text = "Complete Speech"
                    button.background_color = (0, 0, 1, 1)

                    # Train Model butonunu griye çek ve inaktif yap
                    row["train_button"].background_color = (0.5, 0.5, 0.5, 1)  # Gri renk
                    row["train_button"].disabled = True
                    
                    self.start_recording(participant_name, debater_order_n=i + 1)  # Konuşmacı sırasını ilet
                elif button.text == "Complete Speech":
                    button.text = "Start Recording"
                    button.background_color = (1, 0, 0, 1)
                    self.complete_recording(participant_name, debater_order_n=i + 1)  # Konuşmacı sırasını ilet
                break



    def start_recording(self, participant_name, debater_order_n):
        """Kayıt başlatılır."""
        print(f"Recording started for {participant_name} (Order: {debater_order_n})...")

        def record_audio():
            self.is_recording = True
            self.recording = sd.rec(int(self.fs * 10), samplerate=self.fs, channels=1, dtype='int16')  # 10 saniyelik kayıt
            sd.wait()  # Kayıt tamamlanana kadar bekle
            self.is_recording = False

        # Kayıt işlemini ayrı bir thread üzerinde çalıştır
        Thread(target=record_audio).start()

    def complete_recording(self, participant_name, debater_order_n):
        """Kayıt tamamlanır ve dosya kaydedilir."""
        if self.is_recording:
            print("Recording is still in progress. Please wait.")
            return

        if self.recording is None:
            print("No recording found to save.")
            return

        os.makedirs("../data", exist_ok=True)  # Kaydedilecek dizin oluşturuluyor
        file_path = f"../data/{self.debate_id}-{debater_order_n}-{participant_name}.wav"
        write(file_path, self.fs, self.recording)  # Kaydı .wav formatında kaydet

        print(f"Recording saved for {participant_name} (Order: {debater_order_n}) at {file_path}")

        # Train Model butonunu aktif yap
        for row in self.participant_rows:
            if row["label"].text == participant_name:
                row["train_button"].background_color = (1, 1, 0, 1)  # Sarı renk
                row["train_button"].disabled = False
                break

    def create_model(self, input_dim):
        """Modeli oluşturur."""
        model = Sequential()
        model.add(Dense(128, input_dim=input_dim, activation='relu'))  # İlk katman
        model.add(Dense(64, activation='relu'))  # İkinci katman
        model.add(Dense(32, activation='relu'))  # Üçüncü katman
        model.add(Dense(1, activation='sigmoid'))  # Çıktı katmanı (ikili sınıflama)

        model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
        return model

    def train_model(self, button, participant_name):
        """Modeli eğitir."""
        os.chdir(os.path.dirname(os.path.abspath(__file__)))  # Dizini ayarla
        button.text = "Training..."
        print(f"Training model for {participant_name}...")

        # Eğitim verileri için ses dosyalarını topla
        def collect_training_data():
            # Debateler dizinini ve ses dosyalarını belirt
            debate_directory = "../data"
            training_data = []
            labels = []

            # Ses dosyalarını al
            for i, row in enumerate(self.participant_rows):
                if row["label"].text == participant_name:
                    debater_order_n = i + 1  # Konuşmacı sırası
                    break

            # Ses dosyalarını yükle ve etiketle
            participant_files = [f"{self.debate_id}-{debater_order_n}-{participant_name}.wav"]
            for file_name in participant_files:
                file_path = os.path.join(debate_directory, file_name)
                if os.path.exists(file_path):
                    # Ses dosyasını yükle
                    audio, sr = librosa.load(file_path, sr=None)  # Örnekleme oranını olduğu gibi al
                    mfccs = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13)  # MFCC özellik çıkarımı
                    mfccs = np.mean(mfccs, axis=1)  # Ortalamayı al
                    training_data.append(mfccs)
                    labels.append(participant_name)
                else:
                    print(f"Warning: {file_path} does not exist!")

            if not training_data:
                print("No training data found!")
                return

            # Etiketleri sayısal verilere dönüştür
            label_encoder = LabelEncoder()
            labels_encoded = label_encoder.fit_transform(labels)

            # Veriyi numpy array'ine dönüştür
            training_data = np.array(training_data)
            labels_encoded = np.array(labels_encoded)

            # Modeli eğit (Basit bir MLP örneği)
            model = self.create_model(training_data.shape[1])
            model.fit(training_data, labels_encoded, epochs=10, batch_size=32)

            # Eğitim tamamlandığında butonu güncelle
            self.on_training_complete(button, participant_name)

        # Eğitim işlemi simülasyonu
        Thread(target=collect_training_data).start()

    def on_training_complete(self, button, participant_name):
        """Eğitim tamamlandıktan sonra yapılacak işlemler."""
        button.text = "Train Completed"
        button.background_color = (0, 0, 0, 1)  # Siyah renk

        # Status güncelle
        for row in self.participant_rows:
            if row["label"].text == participant_name:
                row["status_label"].text = "Model Trained"
                break

        print("Training complete!")
