/**
 * Live Price Charts Management.
 * Uses Chart.js to render real-time line charts for each stock.
 * Maintains a sliding window of data and dynamically updates colors based on price action.
 */

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
                borderColor: '#4ade80', // Default green
                borderWidth: 2,
                tension: 0.1, // Slight curve to the line
                pointRadius: 0, // Hide points for a cleaner "ticker" look
                pointHoverRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: { mode: 'index', intersect: false }
            },
            scales: {
                x: { 
                    display: false // Hide X-axis labels to save space
                },
                y: { 
                    position: 'right', // Standard financial layout
                    grid: { color: '#1f2937' }, // Dark grid lines
                    ticks: { color: '#9ca3af' } // Light text
                }
            },
            // Disable animations for real-time performance
            animation: { duration: 0 },
            hover: { animationDuration: 0 },
            responsiveAnimationDuration: 0
        }
    });
}

// Initialize all 4 charts once the DOM is ready
document.addEventListener("DOMContentLoaded", () => {
    initChart('chart-AAPL', 'AAPL');
    initChart('chart-TSLA', 'TSLA');
    initChart('chart-GOOGL', 'GOOGL');
    initChart('chart-AMZN', 'AMZN');
});

/**
 * Called externally (from socket.js) whenever a new stock price arrives.
 */
function updateChart(symbol, price, timestamp) {
    const chart = charts[symbol];
    if (!chart) return; // Ignore if we don't have a chart for this symbol

    // 1. Track the "open" price (the first price we receive for this session)
    if (openPrices[symbol] === undefined) {
        openPrices[symbol] = price;
    }

    // 2. Determine color (Green if >= open, Red if < open)
    const openPrice = openPrices[symbol];
    const isUp = price >= openPrice;
    chart.data.datasets[0].borderColor = isUp ? '#4ade80' : '#f87171';

    // 3. Add new data point
    // Convert ISO timestamp to a readable time format
    const dateObj = new Date(timestamp);
    const timeLabel = dateObj.toLocaleTimeString([], { hour12: false });
    
    chart.data.labels.push(timeLabel);
    chart.data.datasets[0].data.push(price);

    // 4. Maintain the sliding window size
    if (chart.data.labels.length > MAX_DATA_POINTS) {
        chart.data.labels.shift();
        chart.data.datasets[0].data.shift();
    }

    // 5. Render
    chart.update();
}