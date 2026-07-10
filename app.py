import sys
import subprocess
from flask import Flask, render_template, request, Response, jsonify
import os

app = Flask(__name__, static_folder='static', template_folder='templates')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/browse')
def browse():
    browse_type = request.args.get('type', 'file')
    try:
        if browse_type == 'folder':
            cmd = ['osascript', '-e', 'POSIX path of (choose folder with prompt "Select Folder")']
        else:
            # allow multiple types if needed, but basic choose file is fine
            cmd = ['osascript', '-e', 'POSIX path of (choose file with prompt "Select Video File")']
            
        # Run osascript
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            path = result.stdout.strip()
            return jsonify({"path": path})
        else:
            return jsonify({"error": "User cancelled or error"}), 400
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
                yield f"data: [ERROR] Process exited with code {return_code}\n\n"
                
        except Exception as e:
            yield f"data: [ERROR] Failed to start process: {str(e)}\n\n"

    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    # Run locally on port 5050
    print("🚀 Archiver Dashboard starting on http://127.0.0.1:5050")
    app.run(debug=True, port=5050, use_reloader=False)
