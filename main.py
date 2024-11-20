import sqlite3
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.checkbox import CheckBox
import os


# Veritabanı bağlantısı
def get_db_connection():
    # Aktif dizini ayarlıyoruz
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    try:
        conn = sqlite3.connect('data/database.db')  # Veritabanı dosyasına bağlanıyoruz
        conn.row_factory = sqlite3.Row  # Sütun isimlerine dictionary tarzında erişebilmek için row_factory ayarını yapıyoruz
        return conn
    except sqlite3.Error as e:
        print(f"Veritabanı hatası: {e}")
        return None


class MainScreen(Screen):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Başlık
        self.layout.add_widget(Label(text="Saved Debates", size_hint_y=None, height=40, font_size=30, bold=True))

        # Saved debates kısmı
        self.load_debates()

        self.add_widget(self.layout)

    def load_debates(self):
        self.layout.clear_widgets()
        conn = get_db_connection()
        if conn is None:
            self.layout.add_widget(Label(text="Unable to open database", size_hint_y=None, height=40))
            return
        
        cursor = conn.cursor()

        # Veritabanından münazaraları çekiyoruz
        cursor.execute("SELECT debate_id, debate_title, debate_school, debate_datetime FROM debates")
        debates = cursor.fetchall()
        conn.close()

        self.layout.add_widget(Label(text="Saved Debates", size_hint_y=None, height=40, bold=True, font_size='20sp'))

        # Münazara yoksa
        if not debates:
            self.layout.add_widget(Label(text="No debates found", size_hint_y=None, height=40))
        else:
            # Münazaralar varsa her birini checkbox olarak ekle
            for debate in debates:
                debate_info = f"{debate['debate_title']} - {debate['debate_school']} - {debate['debate_datetime']}"

                # Checkboxlar için BoxLayout
                debate_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
                checkbox = CheckBox(group='debates', size_hint_x=None, width=50)
                debate_button_label = Label(text=debate_info, size_hint_x=1)
                debate_layout.add_widget(checkbox)
                debate_layout.add_widget(debate_button_label)

                # Checkbox seçildiğinde debate_id ile işlem yapılacak
                checkbox.bind(on_press=lambda btn, debate_id=debate['debate_id']: self.on_debate_select(btn, debate_id))

                self.layout.add_widget(debate_layout)

            # Butonlar arasında boşluk bırakıyoruz
            self.layout.add_widget(Label(text="", size_hint_y=None, height=50))  # Boşluk ekliyoruz

            # 3 sütunlu layout ekliyoruz: Remove, New, Open Debate butonları
            three_columns_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)
            remove_button = Button(text="Remove Debate", size_hint_x=1, background_color=(0.8, 0, 0, 1))
            open_button = Button(text="Open Debate", size_hint_x=1, background_color=(0, 0.8, 0, 1))
            new_button = Button(text="New Debate", size_hint_x=1, background_color=(0, 0.6, 0.8, 1))

            remove_button.bind(on_press=self.remove_debate)
            new_button.bind(on_press=self.start_new_debate)
            open_button.bind(on_press=self.open_debate)

            three_columns_layout.add_widget(remove_button)
            three_columns_layout.add_widget(new_button)
            three_columns_layout.add_widget(open_button)

            self.layout.add_widget(three_columns_layout)

    def on_debate_select(self, instance, debate_id):
        # Seçilen münazara ile debate'yi belirle
        self.selected_debate_id = debate_id

    def start_new_debate(self, instance):
        # Yeni münazara başlatmak için basics.py'e geçiş
        self.manager.current = 'basics_screen'
        self.manager.get_screen('basics_screen').set_debate_info(None)  # Boş bilgi gönderiyoruz

    def remove_debate(self, instance):
        # Seçilen debate'yi sil
        if hasattr(self, 'selected_debate_id'):
            conn = get_db_connection()
            if conn is None:
                self.layout.add_widget(Label(text="Unable to open database for removal", size_hint_y=None, height=40))
                return
            
            cursor = conn.cursor()
            cursor.execute("DELETE FROM debates WHERE debate_id=?", (self.selected_debate_id,))
            conn.commit()
            conn.close()

            # Ekranı güncelle
            self.manager.get_screen('main').load_debates()

    def open_debate(self, instance):
        # Seçilen debate'yi aç
        if hasattr(self, 'selected_debate_id'):
            self.manager.current = 'basics_screen'
            self.manager.get_screen('basics_screen').set_debate_info(self.selected_debate_id)


class ScreenManagement(ScreenManager):
    pass


class MainApp(App):
    def build(self):
        sm = ScreenManagement()
        sm.add_widget(MainScreen(name='main'))
        
        # 'basics' ekranını frontend/basics.py'ye bağladık
        from frontend.basics import BasicsScreen  # basics.py'den import ettik
        from frontend.speechclassification import SpeechClassificationScreen # speechclassification.py'den import ettik
        sm.add_widget(BasicsScreen(name='basics_screen'))  # Burada basics.py'deki BasicsScreen kullanılıyor
        sm.add_widget(SpeechClassificationScreen(name='speech_classification_screen'))
        return sm


if __name__ == '__main__':
    MainApp().run()
