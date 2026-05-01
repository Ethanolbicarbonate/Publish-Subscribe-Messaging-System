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

function updateSubscriberUi(subscriberId, connected) {
    const statusEl = document.getElementById(`status-${subscriberId}`);
    const buttonEl = document.getElementById(`button-${subscriberId}`);
    if (!statusEl || !buttonEl) return;

    statusEl.textContent = connected ? 'Connected' : 'Disconnected';
    statusEl.classList.toggle('connected', connected);
    statusEl.classList.toggle('disconnected', !connected);
    statusEl.classList.toggle('pending', false);

    buttonEl.textContent = connected ? 'Disconnect' : 'Reconnect';
}

async function refreshSubscriberStatuses() {
    try {
        const response = await fetch('/api/subscribers/status');
        if (!response.ok) throw new Error('Status request failed');

        const statuses = await response.json();
        Object.entries(statuses).forEach(([subscriberId, info]) => {
            updateSubscriberUi(subscriberId, info.connected);
        });
    } catch (error) {
        console.warn('[Dashboard] Failed to refresh subscriber statuses.', error);
    }
}

async function controlSubscriber(subscriberId, action) {
    const buttonEl = document.getElementById(`button-${subscriberId}`);
    const statusEl = document.getElementById(`status-${subscriberId}`);
    if (!buttonEl) return;

    buttonEl.disabled = true;
    if (statusEl && action === 'reconnect') {
        statusEl.textContent = 'Reconnecting...';
        statusEl.classList.remove('connected', 'disconnected');
        statusEl.classList.add('pending');
    }

    try {
        const response = await fetch(`/api/subscriber/${encodeURIComponent(subscriberId)}/${action}`, {
            method: 'POST',
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        await response.json();
    } catch (error) {
        console.error('[Dashboard] Subscriber action failed:', error);
    }

    await refreshSubscriberStatuses();
    buttonEl.disabled = false;
}

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-subscriber-id]').forEach((button) => {
        button.addEventListener('click', () => {
            const subscriberId = button.dataset.subscriberId;
            const action = button.textContent.trim().toLowerCase() === 'disconnect' ? 'disconnect' : 'reconnect';
            controlSubscriber(subscriberId, action);
        });
    });

    refreshSubscriberStatuses();
});