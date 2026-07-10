#!/usr/bin/env python3
import os
import sys
import argparse
import subprocess
from pathlib import Path

# Common video extensions to look for when batch processing
SUPPORTED_EXTENSIONS = {'.mkv', '.mp4', '.avi', '.mov', '.flv', '.wmv'}

def encode_video(input_path: Path, output_path: Path, audio_idx: int = None, sub_idx: int = None):
    """
    Encodes a single video file using Apple M1 Hardware (VideoToolbox).
    Target: Brute-force maximum visual quality to match software encoding.
    Video: HEVC 10-bit (hevc_videotoolbox), q:v 60 (very high quality).
    Audio: Opus at 192k.
    Subtitles: Copied as-is.
    """
    print(f"\n[{'='*50}]")
    print(f"Starting HARDWARE encode for: {input_path.name}")
    print(f"Output will be saved to: {output_path}")
    print(f"[{'='*50}]\n")

    # ffmpeg command with maximum quality settings for Apple Silicon hardware
    cmd = [
        "ffmpeg",
        "-nostdin",
        "-i", str(input_path)
    ]
    
    # Map tracks based on user input
    if audio_idx is not None and sub_idx is not None:
        cmd.extend([
            "-map", "0:v:0",                       # Keep first video stream
            "-map", f"0:a:{audio_idx}",            # Keep selected audio track
            "-map", f"0:s:{sub_idx}",              # Keep selected subtitle track
            "-map", "0:t?",                        # Keep all font attachments
            "-disposition:a:0", "default",         # Force audio track to default
            "-disposition:s:0", "default",         # Force subtitle track to default
        ])
    else:
        cmd.extend(["-map", "0"]) # Map all streams natively

    cmd.extend([
        "-c:v", "hevc_videotoolbox",
        "-q:v", "50", # Standard HD Constant Quality target
        "-profile:v", "main10", # Explicitly lock 10-bit profile
        "-spatial_aq", "1", # Hardware Adaptive Quantization (prevents banding in skies/dark rooms)
        "-bf", "4", # Hardware B-Frames (increases compression efficiency for low-motion scenes)
        "-prio_speed", "0", # Force hardware to prioritize quality over speed
        "-power_efficient", "0", # Disable low-power mode, use maximum energy/compute
        "-max_ref_frames", "8", # Double reference frames for better motion tracking
        "-color_primaries", "bt709", # Strict Rec.709 color metadata
        "-color_trc", "bt709",
        "-colorspace", "bt709",
        "-pix_fmt", "p010le", # 10-bit color format specifically required for Apple Hardware
        "-tag:v", "hvc1", # Ensure maximum compatibility with Apple devices (Quicktime, Apple TV)
        "-c:a", "libopus",
        "-b:a", "192k",
        "-c:s", "copy",
        "-y", # Overwrite output if exists
        str(output_path)
    ])

    try:
        # Run ffmpeg, letting its output stream to the terminal
        subprocess.run(cmd, check=True)
        print(f"\n[SUCCESS] Successfully encoded: {output_path.name}")
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] FFmpeg failed with error code {e.returncode} for file {input_path.name}", file=sys.stderr)
    except FileNotFoundError:
        print("\n[ERROR] FFmpeg is not installed or not found in your system PATH.", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="High-Quality Hardware Anime Encoder (M1 Media Engine)")
    parser.add_argument("input", help="Path to a single video file or a directory containing videos.")
    parser.add_argument("-o", "--output", help="Optional output directory. Defaults to a new 'encoded_hw' folder in the input's directory.")
    parser.add_argument("-a", "--audio", type=int, help="Optional audio track index to extract (e.g., 0, 1). Defaults to mapping all tracks.")
    parser.add_argument("-s", "--sub", type=int, help="Optional subtitle track index to extract (e.g., 0, 1). Defaults to mapping all tracks.")
    args = parser.parse_args()

    input_path = Path(args.input).resolve()

    if not input_path.exists():
        print(f"Error: Input path does not exist: {input_path}", file=sys.stderr)
        sys.exit(1)

    # Determine output directory
    if args.output:
        output_dir = Path(args.output).resolve()
    else:
        if input_path.is_file():
            output_dir = input_path.parent / "encoded_hw"
        else:
            output_dir = input_path / "encoded_hw"
            
    output_dir.mkdir(parents=True, exist_ok=True)

    if input_path.is_file():
        # Single file encode
        output_file = output_dir / f"{input_path.stem}_hw.mkv"
        encode_video(input_path, output_file, args.audio, args.sub)
    elif input_path.is_dir():
        # Batch directory encode
        print(f"Scanning directory: {input_path} for supported video files...")
        files_to_encode = [f for f in input_path.iterdir() if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS]
        
        if not files_to_encode:
            print(f"No supported video files found in {input_path}")
            sys.exit(0)
            
        print(f"Found {len(files_to_encode)} file(s) to encode.")
        for i, file_path in enumerate(sorted(files_to_encode), 1):
            print(f"\nProcessing file {i}/{len(files_to_encode)}...")
            output_file = output_dir / f"{file_path.stem}_hw.mkv"
            encode_video(file_path, output_file, args.audio, args.sub)

if __name__ == "__main__":
    main()
