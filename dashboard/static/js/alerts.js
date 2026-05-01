function addAlert(alertData) {
    const list = document.getElementById('alert-list');
    const li = document.createElement('li');
    li.className = `alert-item ${alertData.severity}`;
    
    const time = new Date(alertData.timestamp).toLocaleTimeString([], { hour12: false });
    
    // Select the right Phosphor icon based on severity
    let iconClass = "ph-info";
    if (alertData.severity === "critical") iconClass = "ph-fill ph-warning-octagon";
    if (alertData.severity === "warning") iconClass = "ph-fill ph-warning";
    if (alertData.severity === "success") iconClass = "ph-fill ph-check-circle";
    
    li.innerHTML = `
        <div class="alert-icon-wrapper">
            <i class="${iconClass}"></i>
        </div>
        <div class="alert-content">
            <div class="alert-header">
                <span class="alert-stock">${alertData.symbol}</span>
                <span class="alert-time">${time}</span>
            </div>
            <div class="alert-message">${alertData.message}</div>
        </div>
    `;
    
    list.prepend(li);
    
    if (list.children.length > 20) {
        list.lastElementChild.remove();
    }
    
    triggerPanelFlash(alertData.severity);
}

function triggerPanelFlash(severity) {
    const panel = document.querySelector('.panel-alerts');
    panel.classList.remove('flash-warning', 'flash-critical', 'flash-success');
    void panel.offsetWidth; 
    panel.classList.add(`flash-${severity}`);
    setTimeout(() => {
        panel.classList.remove(`flash-${severity}`);
    }, 600);
}