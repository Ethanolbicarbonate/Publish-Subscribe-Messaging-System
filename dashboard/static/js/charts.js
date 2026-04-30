const MAX_DATA_POINTS = 30;
const charts = {};
const openPrices = {};

function initChart(canvasId, symbol) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    charts[symbol] = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: symbol,
                data: [],
                borderColor: '#10b981', // Tailwind Green
                borderWidth: 2,
                tension: 0.2, // Smoother curve
                pointRadius: 0, 
                pointHoverRadius: 4,
                fill: true, // Enable gradient fill underneath
                backgroundColor: 'rgba(16, 185, 129, 0.1)' // Default light green fill
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: { 
                    mode: 'index', 
                    intersect: false,
                    backgroundColor: 'rgba(24, 24, 27, 0.9)',
                    titleFont: { family: 'Inter', size: 13 },
                    bodyFont: { family: 'Fira Code', size: 12 },
                    padding: 10,
                    borderColor: '#3f3f46',
                    borderWidth: 1
                }
            },
            scales: {
                x: { display: false },
                y: { 
                    position: 'right',
                    grid: { color: '#27272a', drawBorder: false }, 
                    ticks: { color: '#71717a', font: { family: 'Fira Code', size: 10 } } 
                }
            },
            animation: { duration: 0 },
            hover: { animationDuration: 0 },
            responsiveAnimationDuration: 0
        }
    });
}

document.addEventListener("DOMContentLoaded", () => {
    initChart('chart-AAPL', 'AAPL');
    initChart('chart-TSLA', 'TSLA');
    initChart('chart-GOOGL', 'GOOGL');
    initChart('chart-AMZN', 'AMZN');
});

function updateChart(symbol, price, timestamp) {
    const chart = charts[symbol];
    if (!chart) return; 

    if (openPrices[symbol] === undefined) {
        openPrices[symbol] = price;
    }

    const openPrice = openPrices[symbol];
    const isUp = price >= openPrice;
    
    // Create dynamic gradient based on color
    const ctx = chart.ctx;
    const gradient = ctx.createLinearGradient(0, 0, 0, chart.height);
    
    if (isUp) {
        chart.data.datasets[0].borderColor = '#10b981'; // Green
        gradient.addColorStop(0, 'rgba(16, 185, 129, 0.3)');
        gradient.addColorStop(1, 'rgba(16, 185, 129, 0.0)');
    } else {
        chart.data.datasets[0].borderColor = '#ef4444'; // Red
        gradient.addColorStop(0, 'rgba(239, 68, 68, 0.3)');
        gradient.addColorStop(1, 'rgba(239, 68, 68, 0.0)');
    }
    
    chart.data.datasets[0].backgroundColor = gradient;

    const dateObj = new Date(timestamp);
    const timeLabel = dateObj.toLocaleTimeString([], { hour12: false });
    
    chart.data.labels.push(timeLabel);
    chart.data.datasets[0].data.push(price);

    if (chart.data.labels.length > MAX_DATA_POINTS) {
        chart.data.labels.shift();
        chart.data.datasets[0].data.shift();
    }

    chart.update();
}