const socket = io();

const statusDot = document.getElementById('socket-status-dot');
const statusText = document.getElementById('socket-status-text');
const connectedClientsEl = document.getElementById('metric-connected-clients');
const connectedClientsCard = document.getElementById('metric-connected-clients-card');
const subscriptionPatternsEl = document.getElementById('metric-subscription-patterns');
const subscriptionPatternsCard = document.getElementById('metric-subscription-patterns-card');
const activeTopicsEl = document.getElementById('metric-active-topics');
const activeTopicsCard = document.getElementById('metric-active-topics-card');
const messagesSeenEl = document.getElementById('metric-messages-seen');
const pendingAcksEl = document.getElementById('metric-pending-acks');
let messagesSeenCount = 0;

function formatClientsTooltip(clientList = [], subscriptions = {}) {
    if (!clientList.length) return 'No connected clients';
    return clientList.map((clientId) => {
        const patterns = subscriptions[clientId] || [];
        const suffix = patterns.length ? `: ${patterns.join(', ')}` : '';
        return `${clientId}${suffix}`;
    }).join('\n');
}

function formatSubscriptionPatternsTooltip(patterns = []) {
    if (!patterns.length) return 'No subscription patterns';
    return patterns.join('\n');
}

function formatActiveTopicsTooltip(topics = []) {
    if (!topics.length) return 'No active topics';
    return topics.join('\n');
}

socket.on('connect', () => {
    statusDot.classList.remove('offline');
    statusDot.classList.add('online');
    statusText.innerText = 'Connected';
});

function updateBrokerMetrics(stats) {
    if (connectedClientsEl) {
        connectedClientsEl.textContent = String(stats.connected_clients ?? 0);
    }
    if (subscriptionPatternsEl) {
        subscriptionPatternsEl.textContent = String(stats.subscription_patterns ?? 0);
    }
    if (activeTopicsEl) {
        activeTopicsEl.textContent = String(stats.active_published_topics ?? 0);
    }
    if (pendingAcksEl) {
        pendingAcksEl.textContent = String(stats.pending_acks ?? 0);
    }
    if (connectedClientsCard) {
        connectedClientsCard.title = formatClientsTooltip(stats.connected_clients_list || [], stats.client_subscriptions || {});
    }
    if (subscriptionPatternsCard) {
        subscriptionPatternsCard.title = formatSubscriptionPatternsTooltip(stats.subscription_patterns_list || []);
    }
    if (activeTopicsCard) {
        activeTopicsCard.title = formatActiveTopicsTooltip(stats.active_published_topics_list || []);
    }
}

socket.on('broker_stats_update', (stats) => {
    updateBrokerMetrics(stats);
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

    messagesSeenCount += 1;
    if (messagesSeenEl) {
        messagesSeenEl.textContent = String(messagesSeenCount);
    }
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