import sqlite3
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen
from datetime import datetime
import os


# Veritabanı bağlantısı
def get_db_connection():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    conn = sqlite3.connect('../data/database.db')  # Veritabanı dosyasına bağlanıyoruz
    conn.row_factory = sqlite3.Row  # Sütun isimlerine dictionary tarzında erişebilmek için row_factory ayarını yapıyoruz
    return conn


class BasicsScreen(Screen):
    def __init__(self, **kwargs):
        super(BasicsScreen, self).__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Debate bilgilerini gösterecek label
        self.debate_info_label = Label(text="New Debate", size_hint_y=None, height=40, font_size=30)
        self.layout.add_widget(self.debate_info_label)

        # Debate Title input
        self.title_label = Label(text="Debate Title:", size_hint_y=None, height=30)
        self.layout.add_widget(self.title_label)
        self.title_input = TextInput(size_hint_y=None, height=40, multiline=False)
        self.layout.add_widget(self.title_input)

        # Debate School input
        self.school_label = Label(text="Debate School:", size_hint_y=None, height=30)
        self.layout.add_widget(self.school_label)
        self.school_input = TextInput(size_hint_y=None, height=40, multiline=False)
        self.layout.add_widget(self.school_input)

        # Participant count controls
        self.participant_label = Label(text="Participants:", size_hint_y=None, height=30)
        self.layout.add_widget(self.participant_label)

        self.participant_controls = BoxLayout(size_hint_y=None, height=50, spacing=10)
        self.minus_button = Button(text="-", size_hint_x=0.3)
        self.minus_button.bind(on_press=self.decrease_participant_count)
        self.participant_controls.add_widget(self.minus_button)

        self.participant_count_label = Label(text="2", size_hint_x=0.4, halign="center", valign="middle")
        self.participant_count_label.bind(size=self.participant_count_label.setter('text_size'))
        self.participant_controls.add_widget(self.participant_count_label)

        self.plus_button = Button(text="+", size_hint_x=0.3)
        self.plus_button.bind(on_press=self.increase_participant_count)
        self.participant_controls.add_widget(self.plus_button)

        self.layout.add_widget(self.participant_controls)

        # İleri ve Geri Butonları
        button_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)
        self.back_button = Button(text="Back", size_hint_x=0.5, background_color=(0.7, 0, 0, 1))
        self.back_button.bind(on_press=self.go_back)
        button_layout.add_widget(self.back_button)

        self.next_button = Button(text="Next", size_hint_x=0.5, background_color=(0, 0.6, 0, 1))
        self.next_button.bind(on_press=self.save_and_proceed)
        button_layout.add_widget(self.next_button)

        self.layout.add_widget(button_layout)

        self.add_widget(self.layout)

        # Mevcut Debate bilgileri
        self.debate_id = None
        self.participant_count = 2  # Default participant count

    def decrease_participant_count(self, instance):
        """Reduce participant count, minimum is 2."""
        if self.participant_count > 2:
            self.participant_count -= 1
            self.participant_count_label.text = str(self.participant_count)

    def increase_participant_count(self, instance):
        """Increase participant count, maximum is 14."""
        if self.participant_count < 14:
            self.participant_count += 1
            self.participant_count_label.text = str(self.participant_count)

    def set_debate_info(self, debate_id=None, debate_title=None, debate_school=None):
        """
        Kayıtlı bir debate seçilmişse bilgileri doldurur.
        Yeni bir debate ise alanları temizler.
        """
        self.debate_id = debate_id

        if debate_id is not None:  # Kayıtlı debate
            # Debate bilgilerini veritabanından alalım
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM debates WHERE debate_id = ?", (debate_id,))
            debate_data = cursor.fetchone()
            conn.close()

            if debate_data:
                self.debate_info_label.text = f"Editing Debate: {debate_data['debate_title']} | {debate_data['debate_school']}"
                self.title_input.text = debate_data['debate_title']
                self.school_input.text = debate_data['debate_school']
                self.participant_count = debate_data['debate_size']
                self.participant_count_label.text = str(self.participant_count)

                # Alanları düzenlenemez hale getir
                self.title_input.disabled = True
                self.school_input.disabled = True
                self.minus_button.disabled = True
                self.plus_button.disabled = True
            else:
                self.reset_fields()
        else:  # Yeni debate
            self.reset_fields()

        self.debate_info_label.font_size = '18sp'  # Yazı büyüklüğünü ayarla
        self.debate_info_label.bold = True         # Kalın yazı tipi

    def reset_fields(self):
        """Ekran alanlarını sıfırla."""
        self.debate_info_label.text = "New Debate"
        self.title_input.text = ""
        self.school_input.text = ""
        self.participant_count = 2
        self.participant_count_label.text = "2"
        self.title_input.disabled = False
        self.school_input.disabled = False
        self.minus_button.disabled = False
        self.plus_button.disabled = False

    def go_back(self, instance):
        """Ana ekrana geri dön."""
        self.manager.current = 'main'

    def save_and_proceed(self, instance):
        """Debate'i kaydeder ve bir sonraki ekrana geçer."""
        title = self.title_input.text.strip()
        school = self.school_input.text.strip()

        if not title or not school:
            self.debate_info_label.text = "Please fill in all fields!"
            return

        conn = get_db_connection()
        cursor = conn.cursor()

        if self.debate_id is None:  # Yeni debate ekleniyor
            # Sistemdeki zamanı al
            current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Veriyi veritabanına ekle
            cursor.execute("""
                INSERT INTO debates (debate_title, debate_school, debate_datetime, debate_size)
                VALUES (?, ?, ?, ?)
            """, (title, school, current_datetime, self.participant_count))
            conn.commit()

            # Yeni eklenen kaydın ID'sini al
            self.debate_id = cursor.lastrowid

            # Yeni debaters oluştur
            for i in range(1, self.participant_count + 1):
                cursor.execute("""
                    INSERT INTO debaters (debate_id, debater_name, debater_order_n, debater_audio_file_path_name)
                    VALUES (?, ?, ?, ?)
                """, (self.debate_id, f"Person {i}", i, "None"))
            conn.commit()

            self.debate_info_label.text = "Debate saved successfully!"
        else:  # Kayıtlı debate düzenleniyor
            # Debate'in bilgilerini güncelle
            cursor.execute("""
                UPDATE debates
                SET debate_title = ?, debate_school = ?, debate_size = ?
                WHERE debate_id = ?
            """, (title, school, self.participant_count, self.debate_id))
            conn.commit()

            # Eski debaters'ı sil ve yenilerini oluştur
            cursor.execute("DELETE FROM debaters WHERE debate_id = ?", (self.debate_id,))
            for i in range(1, self.participant_count + 1):
                cursor.execute("""
                    INSERT INTO debaters (debate_id, debater_name, debater_order_n, debater_audio_file_path_name)
                    VALUES (?, ?, ?, ?)
                """, (self.debate_id, f"Person {i}", i, "None"))
            conn.commit()

            self.debate_info_label.text = "Debate updated successfully!"

        conn.close()

        # Bir sonraki ekrana geçiş
        self.manager.current = 'speech_classification_screen'

        # Debate bilgilerini SpeechClassificationScreen ekranına aktaralım
        self.manager.get_screen('speech_classification_screen').setup_screen(debate_id=self.debate_id)

