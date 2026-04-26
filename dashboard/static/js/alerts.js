/**
 * Alert Log Management.
 * Renders threshold breach alerts and triggers visual flash animations
 * to draw the user's attention to critical system events.
 */

function addAlert(alertData) {
    const list = document.getElementById('alert-list');
    const li = document.createElement('li');
    
    // Assign a class based on severity ('warning' or 'critical') for styling
    li.className = `alert-item ${alertData.severity}`;
    
    const time = new Date(alertData.timestamp).toLocaleTimeString([], { hour12: false });
    
    li.innerHTML = `
        <div class="alert-header">
            <span class="alert-time">${time}</span>
            <span class="alert-stock">${alertData.stock}</span>
        </div>
        <div class="alert-message">${alertData.message}</div>
    `;
    
    // Prepend to put the newest alerts at the top
    list.prepend(li);
    
    // Cap the alert log at 20 items
    if (list.children.length > 20) {
        list.lastElementChild.remove();
    }
    
    // Trigger a visual flash animation on the entire alert panel
    triggerPanelFlash(alertData.severity);
}

function triggerPanelFlash(severity) {
    const panel = document.querySelector('.panel-alerts');
    
    // Update this line to include 'flash-success'
    panel.classList.remove('flash-warning', 'flash-critical', 'flash-success');
    
    // Force a browser reflow to guarantee the animation restarts
    void panel.offsetWidth; 
    
    // Add the specific flash class
    panel.classList.add(`flash-${severity}`);
    
    // Clean up the class after the animation completes (500ms)
    setTimeout(() => {
        panel.classList.remove(`flash-${severity}`);
    }, 500);
}