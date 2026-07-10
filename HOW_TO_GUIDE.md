# 📖 The Ultimate Encoding Guide

Welcome to your Media Encoding Suite! This guide will walk you through the end-to-end workflow of archiving an anime library using the three custom scripts.

---

## 🧭 Step 1: Choose Your Weapon

You have three separate encoders. Choosing the right one is the secret to perfect archiving.

### 1. Hardware Acceleration (`anime_encoder_hardware.py`)
**Use this for 99% of your library.** 
This script utilizes the Apple Silicon (M1/M2/M3) Media Engine to rip through episodes at blistering speeds (~4 minutes per 24-minute episode).
*   **Pros:** Extremely fast, highly efficient, very low CPU usage.
*   **Cons:** Hardware encoders demand perfect inputs. If the original MKV file has broken timestamps or uses Variable Frame Rate (VFR), the hardware encoder will drop frames and the video will "stutter".

### 2. Software Encoding (`anime_encoder.py`)
**Use this to rescue "stuttering" or cursed episodes.**
This uses the CPU-based `libx265` encoder. 
*   **Pros:** Bulletproof. It will perfectly read broken web-rips and Variable Frame Rate episodes without stuttering. It also uses psycho-visual tuning for slightly better mathematical quality.
*   **Cons:** Very slow (~1-2 hours per episode) and uses 100% of your CPU. 

### 3. Next-Gen AV1 Compression (`anime_encoder_av1.py`)
**Use this for absolute maximum compression on old, grainy episodes.**
*   **Pros:** Uses **Film Grain Synthesis**. It completely removes film grain during the encode (saving massive amounts of space) and artificially recreates it perfectly during playback.
*   **Cons:** Extremely slow (`preset 4`). AV1 is also not natively supported by older Apple devices (though VLC and IINA play it perfectly).

---

## 🎧 Step 2: Track Down Unwanted Audio

Anime web-rips often come with 5+ audio tracks (English, Japanese, Spanish, French, etc.) and 10+ subtitle tracks. If you only want Japanese Audio and English Subtitles, you must find their "Index".

### Finding the Index
1. Open the original `.mkv` file in **VLC Media Player**.
2. Go to **Window > Media Information** (or press `Cmd + I`).
3. Click the **Codec Details** tab.
4. Scroll through the list of Streams.
    *   Find the Japanese audio track. Note its `Stream X` number (e.g., Stream 2). Your Audio Index is **2**.
    *   Find the English subtitle track. Note its `Stream X` number (e.g., Stream 4). Your Subtitle Index is **4**.

*(Note: FFmpeg is zero-indexed, but it indexes audio and subtitles independently. Usually, if VLC says the audio is Stream 2, you can safely pass `-a 2` into the scripts).*

---

## 🚀 Step 3: Run the Encode

### Using the Web Dashboard (Recommended)
1. Open your terminal and run:
   ```bash
   cd /Users/pavannauhwar/Downloads/script/anime_encoder
   python3 app.py
   ```
2. Open `http://127.0.0.1:5050` in your browser.
3. Select your Encoder from the dropdown.
4. Click the **Search** icon next to "Input Target" and select the folder containing your 100+ episodes.
5. Enter your Audio Index and Subtitle Index.
6. Click **Start Encode**. The live terminal will stream the progress directly to your browser!

### Using the Terminal
If you prefer the raw terminal:
```bash
# Strip tracks from a whole folder using Hardware Acceleration
python3 encoders/anime_encoder_hardware.py "/path/to/One Piece Season 9" -a 2 -s 4
```

---

## ⚠️ Troubleshooting Edge Cases

**"I encoded an episode with the hardware script, but the playback stutters when the camera pans!"**
*   **The Cause:** The original episode file has Variable Frame Rate (VFR) or broken timestamps.
*   **The Fix:** Delete the stuttering output. Run that specific episode through the **Software Encoder (`anime_encoder.py`)**. The CPU will mathematically rebuild the broken timestamps and the stutter will vanish.

**"The terminal is spamming `Invalid DTS... replacing by guess`!"**
*   **The Cause:** Apple's VideoToolbox is fighting with the Matroska container over B-frames.
*   **The Fix:** We have specifically removed B-frames from your hardware script to ensure this never happens and your audio stays perfectly synced!
