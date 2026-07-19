import subprocess
import sys
from pathlib import Path
import argparse

def encode_video(input_path, output_dir, audio_idx=None, sub_idx=None):
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_filename = f"{input_path.stem}_av1.mkv"
    output_path = output_dir / output_filename

    print(f"\n[{'='*50}]")
    print(f"Starting SVT-AV1 HOLY GRAIL encode for: {input_path.name}")
    print(f"Output will be saved to: {output_path}")
    print(f"[{'='*50}]\n")

    # ffmpeg command with maximum AV1 Holy Grail parameters
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
        "-c:v", "libsvtav1",
        "-preset", "3", # The absolute limit of practical archival compression (Madness tier)
        "-crf", "20", # Absolute visual perfection and transparency
        "-svtav1-params", "tune=0:enable-qm=1:qm-min=0:qm-max=15:film-grain=12:film-grain-denoise=0:keyint=240:lookahead=120:enable-variance-boost=1:variance-boost-strength=2", # The Ultimate Anime String
        "-pix_fmt", "yuv420p10le", # 10-bit color format to prevent banding
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
    parser = argparse.ArgumentParser(description="AV1 Holy Grail Anime Encoder (SVT-AV1)")
    parser.add_argument("input", help="Path to a single video file or a directory containing videos.")
    parser.add_argument("-o", "--output", help="Optional output directory. Defaults to a new 'encoded_av1' folder in the input's directory.")
    parser.add_argument("-a", "--audio", type=int, help="Optional audio track index to extract (e.g., 0, 1). Defaults to mapping all tracks.")
    parser.add_argument("-s", "--sub", type=int, help="Optional subtitle track index to extract (e.g., 0, 1). Defaults to mapping all tracks.")

    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    
    if not input_path.exists():
        print(f"Error: Input path '{input_path}' does not exist.")
        sys.exit(1)

    if input_path.is_file():
        # Process single file
        output_dir = Path(args.output).resolve() if args.output else input_path.parent / "encoded_av1"
        encode_video(input_path, output_dir, args.audio, args.sub)
    elif input_path.is_dir():
        # Process directory
        output_dir = Path(args.output).resolve() if args.output else input_path / "encoded_av1"
        video_extensions = ['.mkv', '.mp4', '.avi', '.mov']
        videos = [p for p in input_path.iterdir() if p.suffix.lower() in video_extensions]
        
        if not videos:
            print(f"No supported video files found in '{input_path}'")
            sys.exit(0)
            
        print(f"Found {len(videos)} video(s). Starting batch encode...")
        for i, video_path in enumerate(videos, 1):
            print(f"\nProcessing file {i}/{len(videos)}...")
            encode_video(video_path, output_dir, args.audio, args.sub)
            
        print("\n[COMPLETE] Batch encoding finished successfully!")

if __name__ == "__main__":
    main()
