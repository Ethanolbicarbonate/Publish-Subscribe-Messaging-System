const socket = io();

const statusDot = document.getElementById('socket-status-dot');
const statusText = document.getElementById('socket-status-text');

socket.on('connect', () => {
    statusDot.classList.remove('offline');
    statusDot.classList.add('online');
    statusText.innerText = 'Connected';
});

socket.on('disconnect', () => {
    statusDot.classList.remove('online');
    statusDot.classList.add('offline');
    statusText.innerText = 'Disconnected';
});

// Listener 1: Visualizer Data
socket.on('chart_update', (data) => {
    updateChart(data.symbol, data.price, data.timestamp);
});

// Listener 2: Alert Data
socket.on('alert_update', (alertData) => {
    if (typeof addAlert === 'function') addAlert(alertData);
});

// Listener 3: Audit Log Data
socket.on('audit_update', (rawJson) => {
    const list = document.getElementById('firehose-list');
    if(!list) return;

    const li = document.createElement('li');
    li.className = 'firehose-item';
    
    // Quick and dirty JSON syntax highlighting for the UI
    let formatted = JSON.stringify(rawJson)
        .replace(/"([^"]+)":/g, '<span class="key">"$1"</span>:')
        .replace(/"([^"]+)"(,|})/g, '<span class="string">"$1"</span>$2')
        .replace(/([0-9.]+)(,|})/g, '<span class="number">$1</span>$2');

    li.innerHTML = formatted;
    
    list.prepend(li);
    if (list.children.length > 50) list.lastElementChild.remove();
});