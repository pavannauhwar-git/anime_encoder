import sys
import subprocess
from flask import Flask, render_template, request, Response, jsonify
import os
import json
import signal
import webview

app = Flask(__name__, static_folder='static', template_folder='templates')

active_process = None

class Api:
    def __init__(self):
        self.window = None

    def browse(self, browse_type):
        if not self.window:
            return None
        if browse_type == 'folder':
            result = self.window.create_file_dialog(webview.FOLDER_DIALOG)
        else:
            result = self.window.create_file_dialog(webview.OPEN_DIALOG)
        
        if result and len(result) > 0:
            return result[0]
        return None

api = Api()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stop', methods=['POST'])
def stop_process():
    global active_process
    if active_process and active_process.poll() is None:
        active_process.terminate()
        return jsonify({"status": "stopped"})
    return jsonify({"status": "no active process"}), 400

@app.route('/pause', methods=['POST'])
def pause_process():
    global active_process
    if active_process and active_process.poll() is None:
        active_process.send_signal(signal.SIGSTOP)
        return jsonify({"status": "paused"})
    return jsonify({"status": "no active process"}), 400

@app.route('/resume', methods=['POST'])
def resume_process():
    global active_process
    if active_process and active_process.poll() is None:
        active_process.send_signal(signal.SIGCONT)
        return jsonify({"status": "resumed"})
    return jsonify({"status": "no active process"}), 400

@app.route('/tracks')
def tracks():
    file_path = request.args.get('file')
    if not file_path:
        return jsonify({"error": "No file path provided"}), 400
        
    file_path = file_path.strip().strip('\'"')
    
    # If it's a directory, find the first video file
    if os.path.isdir(file_path):
        video_extensions = ['.mkv', '.mp4', '.avi', '.mov', '.flv', '.wmv']
        videos = [os.path.join(file_path, f) for f in os.listdir(file_path) if any(f.lower().endswith(ext) for ext in video_extensions)]
        if not videos:
            return jsonify({"error": "No video files found in directory"}), 404
        videos.sort()
        file_path = videos[0]
        
    cmd = [
        "ffprobe", "-v", "error", 
        "-print_format", "json", 
        "-show_format", "-show_streams", 
        file_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        
        duration = float(data.get('format', {}).get('duration', 0))
        
        audio_tracks = []
        sub_tracks = []
        
        a_idx = 0
        s_idx = 0
        
        for stream in data.get('streams', []):
            codec_type = stream.get('codec_type')
            tags = stream.get('tags', {})
            title = tags.get('title', '')
            lang = tags.get('language', 'und')
            codec_name = stream.get('codec_name', 'unknown')
            
            if codec_type == 'audio':
                label = f"Track {a_idx} - {lang.upper()} ({codec_name})"
                if title: label += f" - {title}"
                audio_tracks.append({"index": a_idx, "label": label})
                a_idx += 1
            elif codec_type == 'subtitle':
                label = f"Track {s_idx} - {lang.upper()} ({codec_name})"
                if title: label += f" - {title}"
                sub_tracks.append({"index": s_idx, "label": label})
                s_idx += 1
                
        return jsonify({
            "audio": audio_tracks,
            "subtitles": sub_tracks,
            "duration": duration,
            "detected_file": os.path.basename(file_path)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/stream')
def stream():
    encoder = request.args.get('encoder')
    input_path = request.args.get('input')
    if input_path:
        input_path = input_path.strip().strip('\'"')

    output_path = request.args.get('output')
    if output_path:
        output_path = output_path.strip().strip('\'"')

    audio_idx = request.args.get('audio')
    sub_idx = request.args.get('sub')

    if not input_path:
        return Response("data: [ERROR] No input path provided\n\n", mimetype='text/event-stream')

    script_map = {
        'hardware': 'anime_encoder_hardware.py',
        'software_hevc': 'anime_encoder.py',
        'software_av1': 'anime_encoder_av1.py'
    }
    
    script_name = script_map.get(encoder)
    if not script_name:
        return Response("data: [ERROR] Invalid encoder selected\n\n", mimetype='text/event-stream')

    script_path = os.path.join(os.path.dirname(__file__), 'encoders', script_name)

    def generate():
        global active_process
        cmd = [sys.executable, script_path, input_path]
        if output_path:
            cmd.extend(['-o', output_path])
        if audio_idx:
            cmd.extend(['-a', audio_idx])
        if sub_idx:
            cmd.extend(['-s', sub_idx])

        yield f"data: [SYSTEM] Starting command: {' '.join(cmd)}\n\n"
        
        try:
            # universal_newlines=True and bufsize=1 ensures line-buffered text streaming
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            active_process = process

            for line in iter(process.stdout.readline, ''):
                if line:
                    # Replace newlines with HTML compatible breaks if necessary, but SSE handles \n fine.
                    # We strip to avoid double newlines in the SSE stream
                    yield f"data: {line.strip()}\n\n"
                
            process.stdout.close()
            return_code = process.wait()
            
            if return_code == 0:
                yield "data: \n\n"
                yield "data: [SYSTEM] Encode complete!\n\n"
            else:
                yield f"data: \n\n"
                if return_code == -15:
                    yield "data: [SYSTEM] Process was terminated by user.\n\n"
                else:
                    yield f"data: [ERROR] Process exited with code {return_code}\n\n"
                
        except Exception as e:
            yield f"data: [ERROR] Failed to start process: {str(e)}\n\n"
        finally:
            active_process = None

    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    window = webview.create_window('Media Encoding Suite', app, js_api=api, width=1200, height=850, min_size=(900, 600))
    api.window = window
    webview.start()
