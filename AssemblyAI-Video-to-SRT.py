import customtkinter as ctk
from tkinter import filedialog, messagebox
import subprocess
import assemblyai as aai
import os
import threading
from deep_translator import GoogleTranslator

# --- Constants for Professional Subtitles ---
API_KEY_FILE = "api_key.ini"
MAX_CHARS_PER_LINE = 42  
MAX_LINES_PER_BLOCK = 2  
MAX_DURATION_SECONDS = 6.0 
MIN_PAUSE_BETWEEN_BLOCKS = 0.8 

# --- Language Mapping ---
LANGUAGE_NAMES = {
    "EN": "English", "RU": "Russian", "AR": "Arabic", "ES": "Spanish",
    "FR": "French", "DE": "German", "IT": "Italian", "PT": "Portuguese",
    "ZH": "Chinese", "JA": "Japanese", "KO": "Korean", "TR": "Turkish"
}

# Translation Targets (Full Name to ISO Code)
TRANSLATE_TO = {
    "None (Original Only)": None,
    "Arabic": "ar",
    "English": "en",
    "Russian": "ru",
    "French": "fr",
    "Spanish": "es",
    "German": "de",
    "Turkish": "tr"
}

def get_full_language_name(code):
    code_up = code.upper()
    return LANGUAGE_NAMES.get(code_up, f"Unknown ({code_up})")

def format_srt_time(seconds):
    millisec = int((seconds - int(seconds)) * 1000)
    seconds = int(seconds)
    minutes = seconds // 60
    seconds %= 60
    hours = minutes // 60
    minutes %= 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millisec:03d}"

def create_professional_srt(media_path, srt_path, api_key, target_lang_code, log_callback, lang_callback):
    """
    1. Transcribes media.
    2. Saves original SRT.
    3. Translates and saves a separate SRT if target_lang_code is provided.
    """
    try:
        log_callback("--- Starting AI Professional Transcription ---")
        if not os.path.exists(media_path):
            log_callback(f"Error: File '{media_path}' not found.")
            return

        base_name = os.path.basename(media_path)
        file_name, _ = os.path.splitext(base_name)
        temp_audio = f"temp_proc_{file_name}.wav"

        # --- Step 1: Normalize Audio ---
        log_callback("[1/4] Normalizing audio...")
        ffmpeg_cmd = "ffmpeg" # Assumes ffmpeg is in system PATH
        command = [ffmpeg_cmd, "-i", media_path, "-y", "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", temp_audio]
        
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        result = subprocess.run(command, capture_output=True, text=True, startupinfo=startupinfo)
        if result.returncode != 0:
            log_callback(f"FFmpeg Error: {result.stderr}")
            return

        # --- Step 2: AI Transcription ---
        log_callback("[2/4] AI identifying languages and speakers...")
        aai.settings.api_key = api_key
        transcriber = aai.Transcriber()
        config = aai.TranscriptionConfig(speaker_labels=True, language_detection=True)
        
        transcript = transcriber.transcribe(temp_audio, config)
        if transcript.status == aai.TranscriptStatus.error:
            log_callback(f"AssemblyAI Error: {transcript.error}")
            return

        # Display detected language
        detected_code = transcript.json_response.get('language_code', 'en')
        display_name = get_full_language_name(detected_code)
        lang_callback(display_name)
        log_callback(f"Detected: {display_name}")

        if os.path.exists(temp_audio):
            os.remove(temp_audio)

        # --- Step 3: Generate Original SRT ---
        log_callback("[3/4] Generating original SRT layout...")
        
        # Prepare segments for translation to avoid double AI calls
        segments = []
        srt_counter = 1
        
        with open(srt_path, 'w', encoding='utf-8') as f:
            for utterance in transcript.utterances:
                words = utterance.words
                current_block_words = []
                
                for i, word in enumerate(words):
                    current_block_words.append(word)
                    should_split = (i == len(words) - 1)
                    
                    if i < len(words) - 1:
                        if (words[i+1].start - word.end) / 1000 > MIN_PAUSE_BETWEEN_BLOCKS:
                            should_split = True
                    
                    text_preview = " ".join(w.text for w in current_block_words)
                    if len(text_preview) > (MAX_CHARS_PER_LINE * MAX_LINES_PER_BLOCK):
                        should_split = True

                    if should_split:
                        start_t = format_srt_time(current_block_words[0].start / 1000)
                        end_t = format_srt_time(current_block_words[-1].end / 1000)
                        content = " ".join(w.text for w in current_block_words)
                        
                        # Store for translation
                        segments.append({'start': start_t, 'end': end_t, 'text': content})
                        
                        f.write(f"{srt_counter}\n{start_t} --> {end_t}\n{content}\n\n")
                        srt_counter += 1
                        current_block_words = []

        # --- Step 4: Translation (Optional) ---
        if target_lang_code:
            log_callback(f"[4/4] Translating to {target_lang_code.upper()}...")
            translated_path = srt_path.replace(".srt", f"_{target_lang_code.upper()}.srt")
            
            translator = GoogleTranslator(source='auto', target=target_lang_code)
            
            with open(translated_path, 'w', encoding='utf-8') as f_trans:
                for idx, seg in enumerate(segments, 1):
                    try:
                        translated_text = translator.translate(seg['text'])
                        f_trans.write(f"{idx}\n{seg['start']} --> {seg['end']}\n{translated_text}\n\n")
                    except Exception as trans_err:
                        log_callback(f"Translation Error at block {idx}: {trans_err}")
                        f_trans.write(f"{idx}\n{seg['start']} --> {seg['end']}\n{seg['text']}\n\n")

            log_callback(f"✅ Success! Original and Translated SRTs saved.")
            messagebox.showinfo("Finished", f"Process Complete!\nOriginal: {os.path.basename(srt_path)}\nTranslated: {os.path.basename(translated_path)}")
        else:
            log_callback("✅ Success! Original SRT saved.")
            messagebox.showinfo("Finished", "Original SRT generated successfully!")

    except Exception as e:
        log_callback(f"System Error: {str(e)}")
        messagebox.showerror("Error", str(e))

# --- GUI Section ---

class ProfessionalApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AI Subtitler & Translator")
        self.geometry("750x750")
        ctk.set_appearance_mode("dark")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=1)

        # Input Frame
        self.frame = ctk.CTkFrame(self)
        self.frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        self.frame.grid_columnconfigure(1, weight=1)

        # File
        ctk.CTkLabel(self.frame, text="Source File:").grid(row=0, column=0, padx=10, pady=10)
        self.path_entry = ctk.CTkEntry(self.frame, placeholder_text="Select media file...")
        self.path_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        ctk.CTkButton(self.frame, text="Browse", width=80, command=self.browse_file).grid(row=0, column=2, padx=10)

        # API Key
        ctk.CTkLabel(self.frame, text="API Key:").grid(row=1, column=0, padx=10, pady=10)
        self.api_entry = ctk.CTkEntry(self.frame, show="*", placeholder_text="AssemblyAI API Key")
        self.api_entry.grid(row=1, column=1, columnspan=2, padx=10, pady=10, sticky="ew")

        # Translation Selector
        ctk.CTkLabel(self.frame, text="Translate To:").grid(row=2, column=0, padx=10, pady=10)
        self.trans_combo = ctk.CTkComboBox(self.frame, values=list(TRANSLATE_TO.keys()))
        self.trans_combo.grid(row=2, column=1, columnspan=2, padx=10, pady=10, sticky="ew")
        self.trans_combo.set("None (Original Only)")

        # Info Labels
        self.info_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.info_frame.grid(row=1, column=0, padx=20, pady=5, sticky="ew")
        ctk.CTkLabel(self.info_frame, text="Detected Source:", font=("Arial", 13, "bold")).pack(side="left", padx=5)
        self.lang_value = ctk.CTkLabel(self.info_frame, text="None", text_color="#00ced1", font=("Arial", 14, "bold"))
        self.lang_value.pack(side="left", padx=5)

        # Start Button
        self.btn_run = ctk.CTkButton(self, text="Generate Subtitles", command=self.start_process, height=45, fg_color="#1f6aa5", font=("Arial", 13, "bold"))
        self.btn_run.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        # Progress & Logs
        self.progress = ctk.CTkProgressBar(self, mode="indeterminate")
        self.log_box = ctk.CTkTextbox(self, font=("Consolas", 12))
        self.log_box.grid(row=5, column=0, padx=20, pady=20, sticky="nsew")

        self.load_key()

    def browse_file(self):
        f = filedialog.askopenfilename(filetypes=[("Media", "*.mp4 *.mp3 *.mkv *.wav *.mov *.m4a")])
        if f:
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, f)

    def load_key(self):
        if os.path.exists(API_KEY_FILE):
            with open(API_KEY_FILE, 'r') as file:
                self.api_entry.insert(0, file.read().strip())

    def start_process(self):
        path = self.path_entry.get()
        key = self.api_entry.get()
        target_name = self.trans_combo.get()
        target_code = TRANSLATE_TO[target_name]
        
        if not path or not key:
            messagebox.showwarning("Warning", "File and API Key required.")
            return

        with open(API_KEY_FILE, 'w') as f: f.write(key)
        srt_out = os.path.splitext(path)[0] + ".srt"
        
        self.btn_run.configure(state="disabled", text="Processing...")
        self.progress.grid(row=4, column=0, padx=20, pady=10, sticky="ew")
        self.progress.start()
        
        threading.Thread(target=self.worker, args=(path, srt_out, key, target_code), daemon=True).start()

    def worker(self, p, s, k, t):
        create_professional_srt(p, s, k, t, self.log, lambda l: self.after(0, lambda: self.lang_value.configure(text=l)))
        self.btn_run.configure(state="normal", text="Generate Subtitles")
        self.progress.stop()
        self.progress.grid_forget()

    def log(self, msg):
        self.log_box.insert("end", f"{msg}\n")
        self.log_box.see("end")

if __name__ == "__main__":
    app = ProfessionalApp()
    app.mainloop()
