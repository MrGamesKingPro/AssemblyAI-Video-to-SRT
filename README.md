# AssemblyAI-Video-to-SRT
This  GUI tool converts video files into SRT subtitle files. It extracts audio using FFmpeg, transcribes the audio with AssemblyAI, and generates an SRT file with advanced splitting logic for optimal readability.

<img width="715" height="647" alt="Screenshot_2025-09-28_22-36-58" src="https://github.com/user-attachments/assets/7654bf9d-322d-45f3-8a83-187d6bc1aee0" />

This looks like a folder structure.
```bash
├── AssemblyAI-Video-to-SRT-main/
│   └── AssemblyAI-Video-to-SRT.py
├── ffmpeg.exe
└── api_key.ini
```
## Download ##
Or you can download a version without installing the library.

[AssemblyAI-Video-to-SRT](https://github.com/MrGamesKingPro/AssemblyAI-Video-to-SRT/releases/tag/AssemblyAI-Video-to-SRT)


#### **Requirements**

1. **Tool Requirements**
    *  Download `ffmpeg.exe` from [ffmpeg.org/download.html](https://ffmpeg.org/download.html).
    *   Place `ffmpeg.exe` in the same directory where you placed the `app.py` script, or add FFmpeg to your system's PATH.

**2. Python Requirements**
This application requires Python 3.7+ and the following libraries. You can install them using pip:

```bash
pip install customtkinter assemblyai
```

#### **How to Use**

1.  **Get Your AssemblyAI API Key:**
    *   Visit [assemblyai.com](https://www.assemblyai.com) and sign up for a free account.
    *   Log in to your dashboard and copy your API key.

2.  **Run the Application:**
    Execute the Python script:
    ```bash
    python AssemblyAI-Video-to-SRT.py
    ```
3.  **Using the GUI:**
    *   **Select Video File:** Click the "Browse" button next to "Video File" and choose your `.mp4`, `.mkv`, `.mov`, etc. file.
    *   **Save SRT as:** A default `.srt` file name and path will be suggested based on your video. You can change this by clicking "Save As".
    *   **Enter AssemblyAI API Key:** Paste your AssemblyAI API key into the "AssemblyAI API Key" field. (The application will save this key for future use).
    *   **Start Transcription:** Click the "Start Transcription" button.
    *   **Monitor Progress:** The log box will display real-time updates on the audio extraction and transcription process.
    *   **Completion:** A message box will confirm when the SRT file has been successfully created.
