let currentDuration = 0; // In seconds

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('encodeForm');
    const startBtn = document.getElementById('startBtn');
    const pauseBtn = document.getElementById('pauseBtn');
    const resumeBtn = document.getElementById('resumeBtn');
    const stopBtn = document.getElementById('stopBtn');
    
    const terminalOutput = document.getElementById('terminalOutput');
    const terminalContainer = document.getElementById('terminalContainer');
    
    const progressContainer = document.getElementById('progressContainer');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const batchProgressText = document.getElementById('batchProgressText');
    
    const completionBox = document.getElementById('completionBox');
    const completionMessage = document.getElementById('completionMessage');
    const openFolderBtn = document.getElementById('openFolderBtn');
    
    const inputPathField = document.getElementById('inputPath');
    const inputWrapper = inputPathField.parentElement;

    inputPathField.addEventListener('dragover', (e) => {
        e.preventDefault();
        inputWrapper.classList.add('drag-over');
    });

    inputPathField.addEventListener('dragleave', () => {
        inputWrapper.classList.remove('drag-over');
    });

    inputPathField.addEventListener('drop', (e) => {
        e.preventDefault();
        inputWrapper.classList.remove('drag-over');
        
        if (e.dataTransfer.files.length > 0) {
            const file = e.dataTransfer.files[0];
            if (file.path) {
                inputPathField.value = file.path;
                detectTracks(file.path);
            } else {
                const text = e.dataTransfer.getData('text');
                if (text) {
                    inputPathField.value = text;
                    detectTracks(text);
                }
            }
        }
    });

    inputPathField.addEventListener('change', () => {
        if (inputPathField.value) {
            detectTracks(inputPathField.value);
        }
    });

    let currentEventSource = null;

    form.addEventListener('submit', (e) => {
        e.preventDefault();
        
        // UI State
        startBtn.style.display = 'none';
        pauseBtn.style.display = 'flex';
        stopBtn.style.display = 'flex';
        resumeBtn.style.display = 'none';
        
        // Reset Progress Bar
        progressContainer.style.display = currentDuration > 0 ? 'block' : 'none';
        progressBar.style.width = '0%';
        progressText.textContent = '0%';
        
        terminalOutput.innerHTML = '';
        batchProgressText.textContent = '';
        completionBox.style.display = 'none';
        terminalContainer.style.display = 'block';

        // Gather form data
        const formData = new FormData(form);
        const params = new URLSearchParams();
        params.append('encoder', formData.get('encoder'));
        params.append('input', formData.get('inputPath'));
        
        const output = formData.get('outputPath');
        if (output) params.append('output', output);
        
        const audio = formData.get('audioIdx');
        if (audio) params.append('audio', audio);
        
        const sub = formData.get('subIdx');
        if (sub) params.append('sub', sub);

        // Start SSE stream
        const url = `/stream?${params.toString()}`;
        currentEventSource = new EventSource(url);

        currentEventSource.onmessage = (event) => {
            const data = event.data;
            const line = document.createElement('div');
            line.className = 'log-line';
            
            if (data.includes('[SYSTEM]')) {
                line.classList.add('log-system');
            } else if (data.includes('[ERROR]')) {
                line.classList.add('log-error');
            }

            line.textContent = data;
            terminalOutput.appendChild(line);
            
            // Auto scroll to bottom
            terminalOutput.scrollTop = terminalOutput.scrollHeight;
            
            // Parse duration dynamically from ffmpeg logs (handles batch encodes perfectly)
            if (data.includes('Duration: ')) {
                const durMatch = data.match(/Duration:\s*(\d+):(\d+):(\d+\.\d+)/);
                if (durMatch) {
                    const h = parseInt(durMatch[1]);
                    const m = parseInt(durMatch[2]);
                    const s = parseFloat(durMatch[3]);
                    currentDuration = (h * 3600) + (m * 60) + s;
                    progressBar.style.width = '0%';
                    progressText.textContent = '0%';
                }
            }

            // Parse progress: time=00:15:32.45
            if (currentDuration > 0 && data.includes('time=')) {
                const match = data.match(/time=\s*(\d+):(\d+):(\d+\.\d+)/);
                if (match) {
                    const h = parseInt(match[1]);
                    const m = parseInt(match[2]);
                    const s = parseFloat(match[3]);
                    const timeInSeconds = (h * 3600) + (m * 60) + s;
                    
                    let percent = (timeInSeconds / currentDuration) * 100;
                    if (percent > 100) percent = 100;
                    
                    progressBar.style.width = percent.toFixed(1) + '%';
                    progressText.textContent = percent.toFixed(1) + '%';
                }
            }

            // Parse batch progress
            if (data.includes('Processing file')) {
                const batchMatch = data.match(/Processing file (\d+)\/(\d+)/);
                if (batchMatch) {
                    batchProgressText.textContent = `[File ${batchMatch[1]} of ${batchMatch[2]}]`;
                }
            }

            // Stream Finished
            if (data.includes('Encode complete!') || data.includes('Process exited with code') || data.includes('Process was terminated')) {
                const success = !data.includes('Process exited with code') && !data.includes('Process was terminated');
                showCompletionScreen(success);
            }
        };

        currentEventSource.onerror = (error) => {
            console.error('SSE Error:', error);
            const line = document.createElement('div');
            line.className = 'log-line log-error';
            line.textContent = '[SYSTEM] Connection to backend lost.';
            terminalOutput.appendChild(line);
            finishStream();
        };
    });

    function showCompletionScreen(success) {
        finishStream();
        
        terminalOutput.style.display = 'none';
        progressContainer.style.display = 'none';
        completionBox.style.display = 'block';
        
        if (success) {
            completionMessage.textContent = 'All files have been encoded successfully.';
            completionMessage.style.color = '#2C3E50';
        } else {
            completionMessage.textContent = 'Encode failed or was stopped early. Check logs for details.';
            completionMessage.style.color = '#E74C3C';
        }
    }

    function finishStream() {
        if (currentEventSource) {
            currentEventSource.close();
            currentEventSource = null;
        }
        
        startBtn.style.display = 'flex';
        pauseBtn.style.display = 'none';
        resumeBtn.style.display = 'none';
        stopBtn.style.display = 'none';
    }

    openFolderBtn.addEventListener('click', async () => {
        const formData = new FormData(form);
        await fetch('/open_folder', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                input_path: formData.get('inputPath'),
                output_path: formData.get('outputPath')
            })
        });
    });

    pauseBtn.addEventListener('click', async () => {
        await fetch('/pause', { method: 'POST' });
        pauseBtn.style.display = 'none';
        resumeBtn.style.display = 'flex';
    });

    resumeBtn.addEventListener('click', async () => {
        await fetch('/resume', { method: 'POST' });
        resumeBtn.style.display = 'none';
        pauseBtn.style.display = 'flex';
    });

    stopBtn.addEventListener('click', async () => {
        await fetch('/stop', { method: 'POST' });
        // The SSE stream will automatically catch the process exit and call finishStream()
    });
});

// Native Browse Dialog Integration
async function browsePath(targetId, type) {
    if (window.pywebview && window.pywebview.api) {
        try {
            const path = await window.pywebview.api.browse(type);
            if (path) {
                document.getElementById(targetId).value = path;
                if (targetId === 'inputPath') {
                    detectTracks(path);
                }
            }
        } catch (err) {
            console.error('Browse error:', err);
        }
    } else {
        alert("pywebview is not initialized yet.");
    }
}

async function detectTracks(path) {
    const audioSelect = document.getElementById('audioIdx');
    const subSelect = document.getElementById('subIdx');
    
    audioSelect.innerHTML = '<option value="">Detecting tracks...</option>';
    subSelect.innerHTML = '<option value="">Detecting tracks...</option>';
    
    try {
        const response = await fetch(`/tracks?file=${encodeURIComponent(path)}`);
        if (!response.ok) throw new Error('Failed to fetch tracks');
        
        const data = await response.json();
        
        if (data.duration) {
            currentDuration = data.duration;
        } else {
            currentDuration = 0;
        }
        
        // Populate Audio
        audioSelect.innerHTML = '<option value="">Keep All Audio Tracks</option>';
        data.audio.forEach(track => {
            const opt = document.createElement('option');
            opt.value = track.index;
            opt.textContent = track.label;
            audioSelect.appendChild(opt);
        });
        
        // Populate Subtitles
        subSelect.innerHTML = '<option value="">Keep All Subtitle Tracks</option>';
        data.subtitles.forEach(track => {
            const opt = document.createElement('option');
            opt.value = track.index;
            opt.textContent = track.label;
            subSelect.appendChild(opt);
        });
        
    } catch (err) {
        console.error(err);
        populateGenericTracks(audioSelect, 'Audio');
        populateGenericTracks(subSelect, 'Subtitle');
        currentDuration = 0;
    }
}

function populateGenericTracks(selectElement, type) {
    selectElement.innerHTML = '<option value="">Keep All ' + type + ' Tracks</option>';
    for(let i=0; i<=5; i++) {
        const opt = document.createElement('option');
        opt.value = i;
        opt.textContent = `Force Track ${i}`;
        selectElement.appendChild(opt);
    }
}
