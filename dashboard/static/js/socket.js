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

socket.on('new_message', (msg) => {
    if (msg.topic.startsWith('STOCK.') && msg.payload && msg.payload.price) {
        const symbol = msg.topic.split('.').pop();
        updateChart(symbol, msg.payload.price, msg.timestamp);
    }
    addMessageToFeed(msg);
});

socket.on('alert', (alertData) => {
    if (typeof addAlert === 'function') addAlert(alertData);
});

function addMessageToFeed(msg) {
    const list = document.getElementById('message-list');
    const li = document.createElement('li');
    li.className = 'feed-item';
    
    const time = new Date(msg.timestamp).toLocaleTimeString([], { hour12: false });
    const topicHtml = `<span class="topic-tag">${msg.topic}</span>`;
    
    // Highlight the values slightly differently for a cleaner code look
    const payloadHtml = `<span class="payload-data">{ "price": <span>${msg.payload.price}</span>, "vol": <span>${msg.payload.volume}</span> }</span>`;
    
    li.innerHTML = `<span class="feed-time">${time}</span> ${topicHtml} ${payloadHtml}`;
    
    list.prepend(li);
    if (list.children.length > 50) list.lastElementChild.remove();
}

setInterval(async () => {
    try {
        const response = await fetch('/api/status');
        const stats = await response.json();
        
        document.getElementById('stat-clients').innerText = stats.connected_clients;
        document.getElementById('stat-topics').innerText = stats.active_topics;
        document.getElementById('stat-delivered').innerText = stats.messages_delivered;
        document.getElementById('stat-acks').innerText = stats.pending_acks;
    } catch (error) {
        console.error('Failed to fetch stats:', error);
    }
}, 2000);