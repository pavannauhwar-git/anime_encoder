document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('encodeForm');
    const startBtn = document.getElementById('startBtn');
    const terminalOutput = document.getElementById('terminalOutput');
    const statusIndicator = document.getElementById('statusIndicator');
    
    // Setup drag and drop for input path
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
            } else {
                const text = e.dataTransfer.getData('text');
                if (text) {
                    inputPathField.value = text;
                }
            }
        }
    });

    let currentEventSource = null;

    form.addEventListener('submit', (e) => {
        e.preventDefault();
        
        // Disable button
        startBtn.disabled = true;
        startBtn.style.opacity = '0.5';
        
        // Clear terminal
        terminalOutput.innerHTML = '';
        
        // Update status
        statusIndicator.textContent = 'Running';
        statusIndicator.classList.add('running');

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

            if (data.includes('Encode complete!') || data.includes('Process exited with code')) {
                finishStream();
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

    function finishStream() {
        if (currentEventSource) {
            currentEventSource.close();
            currentEventSource = null;
        }
        startBtn.disabled = false;
        startBtn.style.opacity = '1';
        statusIndicator.textContent = 'Ready';
        statusIndicator.classList.remove('running');
    }
});

// Native Browse Dialog Integration
async function browsePath(targetId, type) {
    try {
        const response = await fetch(`/browse?type=${type}`);
        if (!response.ok) {
            console.log('User cancelled or error occurred');
            return;
        }
        const data = await response.json();
        if (data.path) {
            document.getElementById(targetId).value = data.path;
        }
    } catch (err) {
        console.error('Browse error:', err);
    }
}
