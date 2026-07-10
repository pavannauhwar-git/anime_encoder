# Media Encoding Suite

An enterprise-grade Python suite for archiving and batch-encoding media files (optimized for Anime), featuring a stunning Material 3 Web UI and three powerful encoding pipelines.

## Features

- **Triple-Threat Encoding Pipelines**:
  - `anime_encoder_hardware.py`: Blazing fast M1 Hardware Acceleration (HEVC VideoToolbox).
  - `anime_encoder.py`: Mathematically precise Software Encoding (HEVC libx265) for maximum fidelity and VFR rescue.
  - `anime_encoder_av1.py`: Next-Generation Compression (SVT-AV1) utilizing Film Grain Synthesis for ultimate archival size-to-quality ratio.
- **Track Stripping**: Easily drop unwanted audio and subtitle tracks on the fly.
- **Batch Processing**: Automatically encodes entire folders of MKV, MP4, or AVI files.
- **Premium Web UI**: A beautiful local Flask dashboard with native macOS Finder integration, drag-and-drop support, and live terminal streaming.

## Installation

1. **Clone the repository** (if you haven't already).
2. **Install requirements**:
   ```bash
   pip install flask
   ```
3. **FFmpeg**: Ensure `ffmpeg` is installed on your system and available in your PATH. (On Mac, use `brew install ffmpeg`).

## Usage

### 1. The Web Dashboard (Recommended)
Launch the beautiful Material UI to manage your batch jobs visually.
```bash
python3 app.py
```
Then navigate to `http://127.0.0.1:5050` in your web browser. 

### 2. Command Line Interface (CLI)
You can also run any of the encoders directly from the terminal.

**Basic Encoding:**
```bash
python3 encoders/anime_encoder_hardware.py "/path/to/video.mkv"
```

**Batch Encoding a Folder:**
```bash
python3 encoders/anime_encoder_hardware.py "/path/to/folder_of_episodes/"
```

**Stripping Tracks (Keep Audio Track 1, Subtitle Track 2):**
```bash
python3 encoders/anime_encoder_hardware.py "/path/to/video.mkv" -a 1 -s 2
```

## Directory Structure
```
anime_encoder/
├── app.py                # Flask Web Server
├── encoders/             # Core Python Encoders
│   ├── anime_encoder.py
│   ├── anime_encoder_av1.py
│   └── anime_encoder_hardware.py
├── static/               # CSS and JS for Web UI
│   ├── app.js
│   └── style.css
├── templates/            # HTML templates
│   └── index.html
└── README.md
```
