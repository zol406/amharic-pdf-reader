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
import threading

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
        self.current_audio_file = None
        self.ocr_in_progress = False
        self.cleanup_audio_files()  # Clean up any leftover files from previous sessions

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

    def cleanup_audio_files(self):
        """Clean up any leftover audio files from previous sessions or failed operations"""
        try:
            for file in os.listdir('.'):
                if file.startswith('page_') and file.endswith('.mp3'):
                    try:
                        os.remove(file)
                        logger.info(f"Cleaned up leftover audio file: {file}")
                    except Exception as e:
                        logger.warning(f"Could not remove leftover file {file}: {e}")
        except Exception as e:
            logger.warning(f"Error during audio file cleanup: {e}")

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
        self.ocr_in_progress = False  # Reset OCR flag for new PDF
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

        # Prevent multiple OCR operations running simultaneously
        if self.ocr_in_progress:
            self.status_label.text = "OCR already in progress..."
            return
            
        self.ocr_in_progress = True
        # Run OCR in a separate thread to avoid blocking UI
        threading.Thread(target=self.perform_ocr_threaded, args=(self.pdf_path,), daemon=True).start()

    def perform_ocr_threaded(self, pdf_path):
        """Perform OCR in a separate thread and update UI safely"""
        try:
            # Check if this OCR request is still valid (user hasn't selected a different PDF)
            if pdf_path != self.pdf_path:
                return
                
            images = convert_from_path(pdf_path, poppler_path=None, thread_count=2)
            total_pages = len(images)
            pages = []
            
            for i, image in enumerate(images):
                # Check again if OCR is still valid
                if pdf_path != self.pdf_path:
                    return
                    
                text = pytesseract.image_to_string(image, lang='amh') or ""
                pages.append(text)
                
                # Schedule UI update on main thread
                Clock.schedule_once(lambda dt, page_num=i+1, total=total_pages: 
                                  self.update_ocr_progress(page_num, total), 0)
            
            # Schedule final result update on main thread
            Clock.schedule_once(lambda dt: self.complete_ocr(pages, total_pages, pdf_path), 0)
            
        except Exception as e:
            logger.error(f"OCR failed: {str(e)}")
            # Schedule error update on main thread
            Clock.schedule_once(lambda dt: self.handle_ocr_error(str(e)), 0)

    def update_ocr_progress(self, page_num, total_pages):
        """Update OCR progress on main thread"""
        if self.ocr_in_progress:
            self.status_label.text = f"OCR: Processing page {page_num}/{total_pages}"

    def complete_ocr(self, pages, total_pages, pdf_path):
        """Complete OCR processing on main thread"""
        # Verify this is still the current PDF
        if pdf_path != self.pdf_path:
            self.ocr_in_progress = False
            return
            
        self.pages = pages
        self.total_pages = total_pages
        self.ocr_in_progress = False
        
        if any(page.strip() for page in self.pages):
            self.status_label.text = "OCR completed. Ready to play."
            self.play_button.disabled = False
            self.update_page_navigation()
        else:
            self.status_label.text = "No Amharic text extracted. Check PDF quality."
            self.play_button.disabled = True

    def handle_ocr_error(self, error_message):
        """Handle OCR errors on main thread"""
        self.ocr_in_progress = False
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
        
        # Warn user about very short content that might not be useful
        page_text_clean = self.pages[self.current_page].strip()
        if len(page_text_clean) < 10:
            self.status_label.text = f"Page {self.current_page + 1} has very little text!"
            return
        
        # Clean up any existing audio file first
        self.cleanup_current_audio_file()
        
        self.play_button.disabled = True
        self.pause_button.disabled = False
        self.playing = True
        self.status_label.text = f"Playing page {self.current_page + 1}..."
        
        try:
            self.current_audio_file = f"page_{self.current_page}.mp3"
            page_text = self.pages[self.current_page]
            
            # Handle text length intelligently - don't cut mid-sentence
            if len(page_text) > 3000:
                # Find the last sentence ending before 3000 characters
                truncated_text = page_text[:3000]
                sentence_endings = ['.', '!', '?', '።']  # Include Amharic sentence ending
                last_sentence_end = -1
                for ending in sentence_endings:
                    pos = truncated_text.rfind(ending)
                    if pos > last_sentence_end:
                        last_sentence_end = pos
                
                if last_sentence_end > 500:  # Only truncate if we have a reasonable amount of text
                    page_text = page_text[:last_sentence_end + 1]
                    self.status_label.text = f"Playing page {self.current_page + 1} (truncated)..."
                else:
                    page_text = truncated_text
                    self.status_label.text = f"Playing page {self.current_page + 1} (partial)..."
            
            # Try Amharic first, fall back to auto-detect if that fails
            try:
                tts = gTTS(text=page_text, lang='am', slow=False)
            except Exception as lang_error:
                logger.warning(f"Amharic TTS failed, trying auto-detect: {lang_error}")
                try:
                    tts = gTTS(text=page_text, lang='auto', slow=False)
                except Exception as auto_error:
                    logger.error(f"Auto-detect TTS also failed: {auto_error}")
                    raise auto_error
            
            tts.save(self.current_audio_file)
            
            self.sound = SoundLoader.load(self.current_audio_file)
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
            self.cleanup_current_audio_file()
            self.stop_audio()

    def cleanup_current_audio_file(self):
        """Clean up the current audio file if it exists"""
        if self.current_audio_file and os.path.exists(self.current_audio_file):
            try:
                os.remove(self.current_audio_file)
                logger.info(f"Cleaned up audio file: {self.current_audio_file}")
            except Exception as e:
                logger.warning(f"Could not remove audio file {self.current_audio_file}: {e}")
            finally:
                self.current_audio_file = None

    def on_sound_stop(self, instance):
        self.cleanup_current_audio_file()
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
        self.cleanup_current_audio_file()
        self.playing = False
        self.play_button.disabled = False
        self.pause_button.disabled = True
        self.status_label.text = f"Stopped. On page {self.current_page + 1}"

    def on_stop(self):
        """Clean up resources when app is closing"""
        self.stop_audio()
        self.cleanup_audio_files()
        return super().on_stop()

if __name__ == '__main':
    AmharicPDFReaderApp().run()
