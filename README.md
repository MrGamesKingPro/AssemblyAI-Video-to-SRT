# AssemblyAI-Video-to-SRT
This  GUI tool converts video files into SRT subtitle files. It extracts audio using FFmpeg, transcribes the audio with AssemblyAI, and generates an SRT file with advanced splitting logic for optimal readability.

<img width="715" height="647" alt="Screenshot_2025-09-28_22-36-58" src="https://github.com/user-attachments/assets/7654bf9d-322d-45f3-8a83-187d6bc1aee0" />


```bash
. This looks like a folder structure.
├── AssemblyAI-Video-to-SRT-main/
│   └── AssemblyAI-Video-to-SRT.py
├── ffmpeg.exe
└── api_key.ini
```
## Download ##
Or you can download a version without installing the library.

[AssemblyAI-Video-to-SRT](https://github.com/MrGamesKingPro/AssemblyAI-Video-to-SRT/releases/tag/AssemblyAI-Video-to-SRT)

#### **Key Features**
*   **AI Auto-Language Detection:** Automatically identifies the spoken language in your media.
*   **Multi-Language Translation:** Seamlessly translates transcriptions into Arabic, French, Spanish, Russian, and more.
*   **Professional SRT Standards:** Enforces global subtitling rules (Max 42 chars/line, 2 lines/block, 6s duration).
*   **Speaker Diarization:** Distinguishes between different speakers for a structured layout.
*   **Zero-Config Dependency Manager:** Automatically installs missing Python libraries on first launch.
*   **Universal Support:** Works with both video (`.mp4`, `.mkv`, etc.) and audio (`.mp3`, `.wav`, etc.).

---

#### **Requirements**

**1. Media Processing Tool (Mandatory)**
*   Download `ffmpeg.exe` from [ffmpeg.org/download.html](https://ffmpeg.org/download.html).
*   **Important:** Place `ffmpeg.exe` in the same folder as the script, or add it to your System PATH.

**2. Python Environment**
*   This application requires **Python 3.8+**.
*   **Note:** The script features **Auto-Installation**. It will automatically attempt to install `customtkinter`, `assemblyai`, and `deep-translator` if they are missing. However, you can install them manually using:
    ```bash
    pip install customtkinter assemblyai deep-translator
    ```

---

#### **Getting Started Guide**

**1. Obtain your AssemblyAI API Key:**
*   Sign up for a free account at [assemblyai.com](https://www.assemblyai.com).
*   Copy your unique **API Key** from the dashboard.

**2. Launch the Application:**
Run the script using the following command:
```bash
python AI-Subtitler-Translator.py
```

**3. Using the Interface:**
*   **Select Media File:** Click **Browse** to choose a video or audio file.
*   **API Key:** Paste your AssemblyAI key. It will be saved locally in `api_key.ini` so you don't have to enter it again.
*   **Select Translation:** Use the **"Translate To"** dropdown menu. Choose "None" for original language only, or select a target language (e.g., Arabic) to generate a second, translated SRT file.
*   **Generate Subtitles:** Click the **"Generate Subtitles"** button.
*   **Monitor Progress:** 
    *   The **Detected Source** label will update once the AI identifies the language.
    *   The **Log Box** provides real-time status updates (Normalization, Transcription, Translation).
*   **Result:** Once finished, a success message will appear. Your SRT files will be saved in the same folder as your source media.

---

#### **Professional Standards Applied**
The tool ensures your subtitles are "Netflix-ready" by applying the following logic:
*   **Line Length:** Breaks lines at 42 characters to prevent screen overcrowding.
*   **Block Limits:** Limits each subtitle to 2 lines maximum.
*   **Timing:** Maintains a minimum 0.8s gap between blocks and a 6s maximum display time for better readability.
