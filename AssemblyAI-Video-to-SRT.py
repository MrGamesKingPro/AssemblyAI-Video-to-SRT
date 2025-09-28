import customtkinter as ctk
from tkinter import filedialog, messagebox
import subprocess
import assemblyai as aai
import os
import threading

# --- Constants ---
# Define the filename for storing the API key.
API_KEY_FILE = "api_key.ini"

# --- Core Transcription and SRT Generation Logic ---

def format_srt_time(seconds):
    """Converts seconds to the standard SRT time format (HH:MM:SS,ms)."""
    millisec = int((seconds - int(seconds)) * 1000)
    seconds = int(seconds)
    minutes = seconds // 60
    seconds %= 60
    hours = minutes // 60
    minutes %= 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millisec:03d}"

def create_speaker_srt(video_path, srt_path, api_key, log_callback):
    """
    Transcribes a video and creates a formatted SRT file with advanced splitting logic.
    This version includes more detailed logging for the GUI.
    """
    try:
        # --- Pre-check and Initial Logging ---
        log_callback("--- Starting New Transcription Process ---")
        if not os.path.exists(video_path):
            log_callback(f"Error: Video file not found at '{video_path}'")
            log_callback("--- Process Halted ---")
            return
        
        log_callback(f"Input Video: {video_path}")
        log_callback(f"Output SRT: {srt_path}")

        base_name = os.path.basename(video_path)
        file_name, _ = os.path.splitext(base_name)
        # Define a temporary path for the extracted audio file.
        audio_path = f"temp_{file_name}.wav"

        # --- [MODIFIED] Step 1: Extract Audio from Video using FFmpeg ---
        log_callback("\n[Step 1/3] Extracting Audio from Video...")
        try:
            # Determine the path for the ffmpeg executable.
            # Prioritize ffmpeg.exe in the same directory as the script/application.
            script_dir = os.path.dirname(os.path.abspath(__file__))
            local_ffmpeg_path = os.path.join(script_dir, "ffmpeg.exe")
            
            ffmpeg_command_name = "ffmpeg" # Default to relying on PATH
            if os.path.exists(local_ffmpeg_path):
                ffmpeg_command_name = local_ffmpeg_path
                log_callback(f"-> Using local ffmpeg executable: {local_ffmpeg_path}")
            else:
                log_callback("-> Local 'ffmpeg.exe' not found. Relying on system PATH for 'ffmpeg'.")

            log_callback(f"-> Creating temporary audio file using ffmpeg: {audio_path}")
            
            # This command extracts audio to a WAV file, which is ideal for AssemblyAI.
            # -y: Overwrite output file if it exists
            # -vn: No video
            # -acodec pcm_s16le: Standard WAV audio codec
            # -ar 16000: Sample rate of 16kHz (good for transcription)
            # -ac 1: Mono audio channel
            command = [
                ffmpeg_command_name, # Use the determined ffmpeg path/name
                "-i", video_path,
                "-y",
                "-vn",
                "-acodec", "pcm_s16le",
                "-ar", "16000",
                "-ac", "1",
                audio_path
            ]
            
            # Execute the command and hide the console window on Windows
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            result = subprocess.run(command, capture_output=True, text=True, check=False, startupinfo=startupinfo)

            # Check if ffmpeg command was successful
            if result.returncode != 0:
                log_callback("--- FFmpeg Error ---")
                log_callback(f"ffmpeg failed with exit code {result.returncode}")
                log_callback("Error Details:")
                log_callback(result.stderr)
                log_callback("--- Please ensure 'ffmpeg.exe' is located in the same directory as this application, or installed and in your system's PATH. ---")
                log_callback("--- Process Halted ---")
                return

            log_callback("-> Audio extracted successfully.")
            log_callback("✅ Step 1 Complete: Audio Extraction Finished.")
        
        except FileNotFoundError:
            log_callback("Error: 'ffmpeg' command not found.")
            log_callback("Please ensure 'ffmpeg.exe' is located in the same directory as this application, or installed and in your system's PATH.")
            log_callback("You can download it from: https://ffmpeg.org/download.html")
            log_callback("--- Process Halted ---")
            messagebox.showerror("FFmpeg Not Found", "ffmpeg is required for audio extraction. Please ensure 'ffmpeg.exe' is in the same directory as this application, or installed and added to your system's PATH.")
            return
        except Exception as e:
            log_callback(f"Error extracting audio: {e}")
            log_callback("--- Process Halted ---")
            return

        # --- Step 2: Transcribe Audio using AssemblyAI ---
        log_callback("\n[Step 2/3] Transcribing Audio with AssemblyAI...")
        try:
            # Configure AssemblyAI with the user-provided API key.
            log_callback("-> Configuring AssemblyAI client with API key...")
            aai.settings.api_key = api_key
            transcriber = aai.Transcriber()
            
            # Set transcription config to get word-level timestamps.
            config = aai.TranscriptionConfig(speaker_labels=False)
            
            log_callback(f"-> Uploading '{os.path.basename(audio_path)}' for transcription...")
            log_callback("(This may take a while depending on file size)")
            transcript = transcriber.transcribe(audio_path, config)

            # Handle potential transcription errors returned by the API.
            log_callback("-> Checking transcription status...")
            if transcript.status == aai.TranscriptStatus.error:
                log_callback(f"Transcription Failed: {transcript.error}")
                log_callback("--- Process Halted ---")
                return
            
            if not transcript.words:
                log_callback("Warning: Could not find any speech or words in the audio.")
                # We don't halt here, just proceed to create an empty SRT.
            
            log_callback("-> Transcription successful.")
            log_callback("✅ Step 2 Complete: Transcription Finished.")

        except Exception as e:
            log_callback(f"Error during transcription: {e}")
            log_callback("--- Process Halted ---")
            return
        finally:
            # Clean up the temporary audio file regardless of success or failure.
            if os.path.exists(audio_path):
                log_callback("-> Cleaning up temporary files...")
                os.remove(audio_path)
                log_callback(f"-> Removed temporary audio file: {audio_path}")

        # --- Step 3: Generate SRT file with Advanced Splitting Logic ---
        log_callback(f"\n[Step 3/3] Generating SRT File at '{srt_path}'...")
        log_callback("-> Applying subtitle formatting and splitting logic...")
        
        # --- SRT Generation Logic ---
        MAX_PAUSE_S = 0.7
        MAX_CHARS = 80
        MAX_DURATION_S = 7
        
        srt_counter = 1
        with open(srt_path, 'w', encoding='utf-8') as f:
            if transcript.words: # Only process if there are words
                current_block_words = []

                for i, word in enumerate(transcript.words):
                    should_start_new_block = False

                    if not current_block_words:
                        current_block_words.append(word)
                        continue

                    prev_word = current_block_words[-1]

                    pause_duration = (word.start - prev_word.end) / 1000
                    if pause_duration >= MAX_PAUSE_S:
                        should_start_new_block = True
                    
                    current_text = " ".join(w.text for w in current_block_words)
                    if len(current_text) + len(word.text) + 1 > MAX_CHARS:
                        should_start_new_block = True

                    block_start_time = current_block_words[0].start
                    block_duration = (word.end - block_start_time) / 1000
                    if block_duration >= MAX_DURATION_S:
                        should_start_new_block = True

                    if should_start_new_block:
                        start_time = format_srt_time(current_block_words[0].start / 1000)
                        end_time = format_srt_time(current_block_words[-1].end / 1000)
                        text = " ".join(w.text for w in current_block_words)
                        
                        f.write(f"{srt_counter}\n")
                        f.write(f"{start_time} --> {end_time}\n")
                        f.write(f"{text}\n\n")
                        
                        srt_counter += 1
                        current_block_words = [word]
                    else:
                        current_block_words.append(word)

                if current_block_words:
                    start_time = format_srt_time(current_block_words[0].start / 1000)
                    end_time = format_srt_time(current_block_words[-1].end / 1000)
                    text = " ".join(w.text for w in current_block_words)
                    
                    f.write(f"{srt_counter}\n")
                    f.write(f"{start_time} --> {end_time}\n")
                    f.write(f"{text}\n\n")
                    srt_counter += 1
        
        log_callback(f"-> Generated {srt_counter - 1} subtitle blocks.")
        log_callback("✅ Step 3 Complete: SRT File Generation Finished.")

        # --- Final Success Message ---
        log_callback("\n-------------------------------------------")
        log_callback("PROCESS COMPLETE!")
        log_callback(f"SRT file has been saved to: {srt_path}")
        messagebox.showinfo("Success", f"SRT file has been created successfully at:\n{srt_path}")

    except Exception as e:
        # --- General Error Handling ---
        error_message = f"An unexpected error occurred: {e}"
        log_callback(error_message)
        log_callback("--- Process Halted due to unexpected error ---")
        messagebox.showerror("Error", error_message)


# --- GUI Application Class ---
class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Window Setup ---
        self.title("AssemblyAI Video to SRT By (MrGamesKingPro)")
        self.geometry("700x600") # Increased height to make space for the progress bar
        # Set the appearance to dark mode (black) and the theme to blue.
        ctk.set_appearance_mode("dark") 
        ctk.set_default_color_theme("blue")

        # --- Layout Configuration ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1) # Make the log box row expandable

        # --- Frame for User Inputs ---
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.input_frame.grid_columnconfigure(1, weight=1)

        # --- Widget Definitions ---

        # Video File Selection
        self.video_label = ctk.CTkLabel(self.input_frame, text="Video File:")
        self.video_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.video_path_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Select a video file...")
        self.video_path_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        self.video_browse_button = ctk.CTkButton(self.input_frame, text="Browse", width=100, command=self.browse_video)
        self.video_browse_button.grid(row=0, column=2, padx=10, pady=5)

        # SRT Save Path
        self.srt_label = ctk.CTkLabel(self.input_frame, text="Save SRT as:")
        self.srt_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.srt_path_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Select a location to save the .srt file...")
        self.srt_path_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        self.srt_browse_button = ctk.CTkButton(self.input_frame, text="Save As", width=100, command=self.browse_srt)
        self.srt_browse_button.grid(row=1, column=2, padx=10, pady=5)

        # API Key Input
        self.api_key_label = ctk.CTkLabel(self.input_frame, text="AssemblyAI API Key:")
        self.api_key_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.api_key_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Enter your API key here...", show="*")
        self.api_key_entry.grid(row=2, column=1, columnspan=2, padx=10, pady=5, sticky="ew")
        
        # --- Start Button ---
        self.start_button = ctk.CTkButton(self, text="Start Transcription", command=self.start_processing_thread)
        self.start_button.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        # --- Progress Bar (NEW FEATURE) ---
        self.progress_bar = ctk.CTkProgressBar(self, mode="indeterminate")
        # The progress bar is not displayed initially; it's shown using .grid() when processing starts.

        # --- Log Box ---
        self.log_box = ctk.CTkTextbox(self, state="disabled", wrap="word")
        self.log_box.grid(row=3, column=0, padx=10, pady=10, sticky="nsew")

        # --- Initial Setup Calls ---
        self.load_api_key() # Load the key on startup.
        self.show_welcome_message() # Show instructions on startup.

    # --- GUI Helper Methods ---

    def browse_video(self):
        """Opens a file dialog to select a video file."""
        file_path = filedialog.askopenfilename(
            title="Select a Video File",
            filetypes=(("Video Files", "*.mp4 *.mkv *.mov *.avi"), ("All files", "*.*"))
        )
        if file_path:
            self.video_path_entry.delete(0, "end")
            self.video_path_entry.insert(0, file_path)
            # Auto-suggest the SRT output path based on the video name.
            srt_path = os.path.splitext(file_path)[0] + ".srt"
            self.srt_path_entry.delete(0, "end")
            self.srt_path_entry.insert(0, srt_path)

    def browse_srt(self):
        """Opens a file dialog to choose where to save the SRT file."""
        file_path = filedialog.asksaveasfilename(
            title="Save SRT File As",
            defaultextension=".srt",
            filetypes=(("SRT files", "*.srt"), ("All files", "*.*"))
        )
        if file_path:
            self.srt_path_entry.delete(0, "end")
            self.srt_path_entry.insert(0, file_path)
            
    def log(self, message):
        """
        Thread-safe method to insert a message into the log box.
        This is passed as a callback to the transcription function.
        """
        self.log_box.configure(state="normal")
        self.log_box.insert("end", message + "\n")
        self.log_box.configure(state="disabled")
        self.log_box.see("end") # Auto-scroll to the bottom.
        self.update_idletasks() # Force UI to refresh immediately.

    def show_welcome_message(self):
        """Displays initial instructions in the log box (NEW FEATURE)."""
        welcome_text = """
Welcome to the SRT Generator!

How to Use:
1. Click 'Browse' to select your video file (.mp4, .mkv, etc.).
2. The 'Save SRT as' path will be suggested automatically. You can change it if you wish.
3. Enter your AssemblyAI API key below. The key will be saved for future use.
4. Click 'Start Transcription' to begin the process.

How to get an AssemblyAI API Key:
1. Go to assemblyai.com and sign up for a free account.
2. After signing in, you will see your API key on your dashboard.
3. Copy the key and paste it into the API key field in this application.

Important: FFmpeg is required for audio extraction. Please ensure 'ffmpeg.exe' is placed in the same directory as this application, or installed and added to your system's PATH. You can download it from: https://ffmpeg.org/download.html

Logs and progress will appear in this box.
-------------------------------------------
"""
        self.log_box.configure(state="normal")
        self.log_box.insert("1.0", welcome_text)
        self.log_box.configure(state="disabled")

    # --- API Key Persistence Methods (NEW FEATURE) ---

    def load_api_key(self):
        """Loads the API key from the local file if it exists."""
        try:
            with open(API_KEY_FILE, 'r') as f:
                api_key = f.read().strip()
                if api_key:
                    self.api_key_entry.insert(0, api_key)
                    self.log(f"Loaded API Key from {API_KEY_FILE}")
        except FileNotFoundError:
            # This is normal if the app is run for the first time.
            self.log("API key file not found. Please enter your key.")
        except Exception as e:
            self.log(f"Error loading API key: {e}")

    def save_api_key(self, api_key):
        """Saves the API key to a local file."""
        try:
            with open(API_KEY_FILE, 'w') as f:
                f.write(api_key)
            self.log(f"API Key saved to {API_KEY_FILE}")
        except Exception as e:
            self.log(f"Error saving API key: {e}")

    # --- Processing and Threading ---

    def start_processing_thread(self):
        """Validates inputs and starts the transcription process in a new thread."""
        video_path = self.video_path_entry.get()
        srt_path = self.srt_path_entry.get()
        api_key = self.api_key_entry.get()

        # Input validation.
        if not video_path or not srt_path or not api_key:
            messagebox.showwarning("Missing Information", "Please fill in all fields before starting.")
            return
        
        # --- UI State: Processing ---
        self.start_button.configure(state="disabled", text="Processing...")
        self.progress_bar.grid(row=2, column=0, padx=10, pady=5, sticky="ew") # Show progress bar.
        self.progress_bar.start()
        
        # Clear log for the new process.
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")
        
        # Save the API key for the next session.
        self.save_api_key(api_key)
        
        # Run the core logic in a separate thread to keep the GUI responsive.
        processing_thread = threading.Thread(
            target=self.run_transcription,
            args=(video_path, srt_path, api_key)
        )
        processing_thread.daemon = True # Allows app to close even if the thread is running.
        processing_thread.start()
        
    def run_transcription(self, video_path, srt_path, api_key):
        """
        Wrapper function that runs in the background thread.
        It calls the main transcription function and handles UI updates upon completion.
        """
        try:
            create_speaker_srt(video_path, srt_path, api_key, self.log)
        finally:
            # --- UI State: Idle ---
            # This 'finally' block ensures the UI is reset even if an error occurs during processing.
            self.start_button.configure(state="normal", text="Start Transcription")
            self.progress_bar.stop()
            self.progress_bar.grid_forget() # Hide the progress bar again.


# --- Main Execution Block ---
if __name__ == '__main__':
    app = App()
    app.mainloop()
