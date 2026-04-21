/**
 * WebSocket Connection & Message Routing.
 * Connects to the Flask-SocketIO server, handles incoming live data,
 * routes prices to the charts, and populates the scrolling message feed.
 */

const socket = io(); // Automatically connects to the host that served the page

// --- Connection Status UI ---
const statusDot = document.getElementById('socket-status-dot');
const statusText = document.getElementById('socket-status-text');

socket.on('connect', () => {
    statusDot.classList.remove('offline');
    statusDot.classList.add('online');
    statusText.innerText = 'Connected';
    console.log('[Socket.IO] Connected to server.');
});

socket.on('disconnect', () => {
    statusDot.classList.remove('online');
    statusDot.classList.add('offline');
    statusText.innerText = 'Disconnected';
    console.log('[Socket.IO] Disconnected from server.');
});

// --- Incoming Message Routing ---
socket.on('new_message', (msg) => {
    // 1. Update the appropriate Chart if it's a stock price
    if (msg.topic.startsWith('STOCK.') && msg.payload && msg.payload.price) {
        const symbol = msg.topic.split('.').pop(); // e.g., 'AAPL'
        updateChart(symbol, msg.payload.price, msg.timestamp);
    }

    // 2. Add to the Live Message Feed
    addMessageToFeed(msg);
});

// --- Incoming Alert Routing ---
socket.on('alert', (alertData) => {
    // Defined in alerts.js
    if (typeof addAlert === 'function') {
        addAlert(alertData);
    }
});

// --- UI Helper Functions ---
function addMessageToFeed(msg) {
    const list = document.getElementById('message-list');
    const li = document.createElement('li');
    li.className = 'feed-item';
    
    const time = new Date(msg.timestamp).toLocaleTimeString([], { hour12: false });
    
    // Create a color-coded span for the topic
    const topicHtml = `<span class="topic-tag">${msg.topic}</span>`;
    // Format the JSON payload nicely
    const payloadHtml = `<span class="payload-data">${JSON.stringify(msg.payload)}</span>`;
    
    li.innerHTML = `<span class="feed-time">[${time}]</span> ${topicHtml} ${payloadHtml}`;
    
    // Prepend puts the newest messages at the top
    list.prepend(li);
    
    // Cap the list at 50 items to prevent the DOM from growing infinitely
    if (list.children.length > 50) {
        list.lastElementChild.remove();
    }
}

// --- Broker Status Polling ---
// Update the stats panel every 2 seconds
setInterval(async () => {
    try {
        const response = await fetch('/api/status');
        const stats = await response.json();
        
        document.getElementById('stat-clients').innerText = stats.connected_clients;
        document.getElementById('stat-topics').innerText = stats.active_topics;
        document.getElementById('stat-delivered').innerText = stats.messages_delivered;
        document.getElementById('stat-acks').innerText = stats.pending_acks;
    } catch (error) {
        console.error('[Dashboard] Failed to fetch broker stats:', error);
    }
}, 2000);