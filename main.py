from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.clock import Clock
from plyer import filechooser
from gtts import gTTS
import PyPDF2
import os
from kivy.core.audio import SoundLoader
import pytesseract
from pdf2image import convert_from_path
import tempfile
import logging

logging.basicConfig(level=logging.INFO, filename='app.log')
logger = logging.getLogger(__name__)

class AmharicPDFReaderApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sound = None
        self.pages = []
        self.current_page = 0
        self.playing = False
        self.pdf_path = None
        self.total_pages = 0

    def build(self):
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        self.status_label = Label(text="Select your Amharic PDF", size_hint=(1, 0.3))
        self.select_button = Button(text="Choose PDF", on_press=self.choose_file, size_hint=(1, 0.15))
        self.play_button = Button(text="Play Page", on_press=self.play_audio, disabled=True, size_hint=(1, 0.15))
        self.pause_button = Button(text="Pause", on_press=self.pause_audio, disabled=True, size_hint=(1, 0.15))
        self.next_page_button = Button(text="Next Page", on_press=self.next_page, disabled=True, size_hint=(1, 0.15))
        self.prev_page_button = Button(text="Previous Page", on_press=self.prev_page, disabled=True, size_hint=(1, 0.15))
        self.speed_slider = Slider(min=0.5, max=2.0, value=1.0, step=0.1, size_hint=(1, 0.1))
        self.speed_label = Label(text="Speed: 1.0x", size_hint=(1, 0.1))
        self.progress_label = Label(text="Page 0 of 0", size_hint=(1, 0.1))
        
        self.layout.add_widget(self.status_label)
        self.layout.add_widget(self.select_button)
        self.layout.add_widget(self.play_button)
        self.layout.add_widget(self.pause_button)
        self.layout.add_widget(self.prev_page_button)
        self.layout.add_widget(self.next_page_button)
        self.layout.add_widget(Label(text="Adjust Speed", size_hint=(1, 0.1)))
        self.layout.add_widget(self.speed_slider)
        self.layout.add_widget(self.speed_label)
        self.layout.add_widget(self.progress_label)
        
        self.speed_slider.bind(value=self.update_speed)
        return self.layout

    def update_speed(self, instance, value):
        self.speed_label.text = f"Speed: {value:.1f}x"
        if self.sound:
            try:
                self.sound.rate = value
            except:
                logger.warning("Speed adjustment not supported")

    def choose_file(self, instance):
        filechooser.open_file(filters=["*.pdf"], on_selection=self.process_pdf)

    def process_pdf(self, selection):
        if not selection:
            self.status_label.text = "No file selected!"
            return
        
        self.pdf_path = selection[0]
        self.status_label.text = f"Processing: {os.path.basename(self.pdf_path)}"
        self.pages = []
        self.current_page = 0
        self.total_pages = 0
        self.play_button.disabled = True
        self.pause_button.disabled = True
        self.next_page_button.disabled = True
        self.prev_page_button.disabled = True

        try:
            with open(self.pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                self.total_pages = len(reader.pages)
                self.pages = [page.extract_text() or "" for page in reader.pages]
                if any(page.strip() for page in self.pages):
                    self.status_label.text = "Text extracted. Ready to play."
                    self.play_button.disabled = False
                    self.update_page_navigation()
                    return
        except Exception as e:
            logger.error(f"Text extraction failed: {str(e)}")
            self.status_label.text = "Scanned PDF detected. Attempting OCR..."

        Clock.schedule_once(lambda dt: self.perform_ocr(self.pdf_path), 0)

    def perform_ocr(self, pdf_path):
        try:
            images = convert_from_path(pdf_path, poppler_path=None, thread_count=2)
            self.total_pages = len(images)
            self.pages = []
            for i, image in enumerate(images):
                text = pytesseract.image_to_string(image, lang='amh') or ""
                self.pages.append(text)
                self.status_label.text = f"OCR: Processing page {i + 1}/{self.total_pages}"
            if any(page.strip() for page in self.pages):
                self.status_label.text = "OCR completed. Ready to play."
                self.play_button.disabled = False
                self.update_page_navigation()
            else:
                self.status_label.text = "No Amharic text extracted. Check PDF quality."
                self.play_button.disabled = True
        except Exception as e:
            logger.error(f"OCR failed: {str(e)}")
            self.status_label.text = f"OCR failed: Check PDF quality or scan clarity."
            self.play_button.disabled = True

    def update_page_navigation(self):
        self.progress_label.text = f"Page {self.current_page + 1} of {self.total_pages}"
        self.next_page_button.disabled = self.current_page >= self.total_pages - 1
        self.prev_page_button.disabled = self.current_page <= 0

    def next_page(self, instance):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.update_page_navigation()
            self.stop_audio()
            self.status_label.text = f"Selected page {self.current_page + 1}"

    def prev_page(self, instance):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_page_navigation()
            self.stop_audio()
            self.status_label.text = f"Selected page {self.current_page + 1}"

    def play_audio(self, instance):
        if not self.pages or not self.pages[self.current_page].strip():
            self.status_label.text = f"No text on page {self.current_page + 1}!"
            return
        
        self.play_button.disabled = True
        self.pause_button.disabled = False
        self.playing = True
        self.status_label.text = f"Playing page {self.current_page + 1}..."
        
        try:
            output_file = f"page_{self.current_page}.mp3"
            tts = gTTS(text=self.pages[self.current_page][:3000], lang='am', slow=False)
            tts.save(output_file)
            
            self.sound = SoundLoader.load(output_file)
            if self.sound:
                try:
                    self.sound.rate = self.speed_slider.value
                except:
                    logger.warning("Speed adjustment not supported")
                self.sound.play()
                self.sound.bind(on_stop=self.on_sound_stop)
            else:
                self.status_label.text = "Error loading audio."
                self.stop_audio()
        except Exception as e:
            logger.error(f"TTS error: {str(e)}")
            self.status_label.text = f"Error: Check internet or PDF content."
            self.stop_audio()

    def on_sound_stop(self, instance):
        try:
            os.remove(f"page_{self.current_page}.mp3")
        except:
            pass
        self.stop_audio()

    def pause_audio(self, instance):
        if self.sound:
            self.sound.stop()
            self.playing = False
            self.play_button.disabled = False
            self.pause_button.disabled = True
            self.status_label.text = f"Paused on page {self.current_page + 1}"

    def stop_audio(self):
        if self.sound:
            self.sound.stop()
            self.sound = None
        self.playing = False
        self.play_button.disabled = False
        self.pause_button.disabled = True
        self.status_label.text = f"Stopped. On page {self.current_page + 1}"

if __name__ == '__main':
    AmharicPDFReaderApp().run()
