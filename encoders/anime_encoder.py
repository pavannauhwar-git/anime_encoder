#!/usr/bin/env python3
import os
import sys
import argparse
import subprocess
from pathlib import Path

# Common video extensions to look for when batch processing
SUPPORTED_EXTENSIONS = {'.mkv', '.mp4', '.avi', '.mov', '.flv', '.wmv'}

def encode_video(input_path: Path, output_path: Path, audio_idx=None, sub_idx=None):
    """
    Encodes a single video file using optimal anime settings.
    Target: 300-500MB for a 24 min episode.
    Video: HEVC 10-bit (libx265), CRF 20, preset slow, with advanced psycho-visual tuning.
    Audio: Opus at 192k.
    Subtitles: Copied as-is.
    """
    print(f"\n[{'='*50}]")
    print(f"Starting encode for: {input_path.name}")
    print(f"Output will be saved to: {output_path}")
    print(f"[{'='*50}]\n")

    # ffmpeg command with optimal settings for anime
    cmd = [
        "ffmpeg",
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
        "-c:v", "libx265",
        "-crf", "20",
        "-preset", "slow",
        "-pix_fmt", "yuv420p10le",
        "-x265-params", "aq-mode=3:aq-strength=0.8:bframes=8:no-sao=1:deblock=-1,-1:psy-rd=1.5:psy-rdoq=2.0:rc-lookahead=60:qcomp=0.65:cbqpoffs=-2:crqpoffs=-2:ref=6:no-strong-intra-smoothing=1:b-intra=1:tu-intra-depth=2:tu-inter-depth=2:subme=4:tskip=1:tskip-fast=1:qg-size=16:keyint=240:min-keyint=24:no-open-gop=1",
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
    parser = argparse.ArgumentParser(description="High-Quality Anime Encoder (HEVC 10-bit / Opus)")
    parser.add_argument("input", help="Path to a single video file or a directory containing videos.")
    parser.add_argument("-o", "--output", help="Optional output directory. Defaults to a new 'encoded' folder in the input's directory.")
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
            output_dir = input_path.parent / "encoded"
        else:
            output_dir = input_path / "encoded"
            
    output_dir.mkdir(parents=True, exist_ok=True)

    if input_path.is_file():
        # Single file encode
        output_file = output_dir / f"{input_path.stem}_encoded.mkv"
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
            output_file = output_dir / f"{file_path.stem}_encoded.mkv"
            encode_video(file_path, output_file, args.audio, args.sub)

if __name__ == "__main__":
    main()
