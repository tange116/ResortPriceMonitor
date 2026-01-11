const CONFIG = {
    csvUrl: window.location.origin + '/history.csv',
};

console.log('📊 Destination Price Monitor - Loading from Vercel');

let priceData = [];
let chart = null;
let currentRange = 30;

// Mask price: show only thousands and above, mask hundreds and below with X
function maskPrice(price) {
    const numPrice = parseInt(price);
    if (isNaN(numPrice)) return '$0';
    
    const thousandPart = Math.floor(numPrice / 1000);
    const remainderPart = numPrice % 1000;
    
    if (remainderPart === 0) {
        return `$${(thousandPart * 1000).toLocaleString()}`;
    }
    
    return `$${thousandPart.toLocaleString()},XXX`;
}

document.addEventListener('DOMContentLoaded', async () => {
    await loadPriceData();
    setupEventListeners();
});

async function loadPriceData() {
    const loadingOverlay = document.getElementById('loadingOverlay');
    
    try {
        const url = CONFIG.csvUrl + `?_=${Date.now()}`;
        
        const response = await fetch(url, {
            method: 'GET',
            cache: 'no-cache'
        });
        
        if (!response.ok) {
            throw new Error(`Failed to fetch CSV: HTTP ${response.status}`);
        }
        
        const csvText = await response.text();
        priceData = parseCSV(csvText);
        
        if (priceData.length === 0) {
            throw new Error('No price data found in CSV');
        }
        
        updateStats();
        createChart();
        
        loadingOverlay.classList.add('hidden');
    } catch (error) {
        console.error('Error loading price data:', error);
        loadingOverlay.innerHTML = `
            <div style="text-align: center; color: #EF4444;">
                <svg width="64" height="64" viewBox="0 0 64 64" fill="none" style="margin-bottom: 16px;">
                    <circle cx="32" cy="32" r="28" stroke="currentColor" stroke-width="4"/>
                    <path d="M32 20V36" stroke="currentColor" stroke-width="4" stroke-linecap="round"/>
                    <circle cx="32" cy="44" r="2" fill="currentColor"/>
                </svg>
                <h2 style="margin-bottom: 8px;">Failed to Load Data</h2>
                <p style="color: #6B7280; margin-bottom: 16px;">Could not fetch price history from GitHub</p>
                <button onclick="location.reload()" style="padding: 10px 20px; background: #4F46E5; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: 600;">
                    Retry
                </button>
            </div>
        `;
    }
}

function parseCSV(csvText) {
    const lines = csvText.trim().split('\n');
    if (lines.length < 2) return [];
    
    const headers = lines[0].split(',');
    
    return lines.slice(1).map(line => {
        const values = line.split(',');
        const row = {};
        headers.forEach((header, index) => {
            row[header.trim()] = values[index]?.trim() || '';
        });
        return row;
    }).filter(row => row.price_check_date);
}

function updateStats() {
    if (priceData.length === 0) return;
    
    const sortedData = [...priceData].sort((a, b) => 
        new Date(b.price_check_date) - new Date(a.price_check_date)
    );
    
    const latest = sortedData[0];
    const previous = sortedData[1];
    
    const currentPrice = parseInt(latest.best_price);
    document.getElementById('currentPrice').textContent = maskPrice(currentPrice);
    
    if (previous) {
        const previousPrice = parseInt(previous.best_price);
        const change = currentPrice - previousPrice;
        const changePercent = ((change / previousPrice) * 100).toFixed(1);
        const changeElement = document.getElementById('priceChange');
        
        if (change > 0) {
            changeElement.className = 'stat-change negative';
            changeElement.innerHTML = `↑ $${Math.abs(change).toLocaleString()} (+${changePercent}%)`;
        } else if (change < 0) {
            changeElement.className = 'stat-change positive';
            changeElement.innerHTML = `↓ $${Math.abs(change).toLocaleString()} (${changePercent}%)`;
        } else {
            changeElement.className = 'stat-change';
            changeElement.textContent = 'No change';
        }
    }
    
    const lowestEntry = priceData.reduce((min, entry) => 
        parseInt(entry.best_price) < parseInt(min.best_price) ? entry : min
    );
    document.getElementById('lowestPrice').textContent = maskPrice(lowestEntry.best_price);
    document.getElementById('lowestDate').textContent = formatDate(lowestEntry.price_check_date);
    
    const last30Days = sortedData.slice(0, Math.min(30, sortedData.length));
    if (last30Days.length > 1) {
        const oldest = last30Days[last30Days.length - 1];
        const trendChange = currentPrice - parseInt(oldest.best_price);
        const trendPercent = ((trendChange / parseInt(oldest.best_price)) * 100).toFixed(1);
        
        document.getElementById('trend').textContent = `${trendPercent}%`;
        const indicator = document.getElementById('trendIndicator');
        
        if (trendChange > 0) {
            indicator.className = 'stat-indicator up';
            indicator.textContent = '↑ Increasing';
        } else if (trendChange < 0) {
            indicator.className = 'stat-indicator down';
            indicator.textContent = '↓ Decreasing';
        } else {
            indicator.className = 'stat-indicator stable';
            indicator.textContent = '→ Stable';
        }
    }
    
    document.getElementById('lastUpdate').textContent = formatDate(latest.price_check_date);
}

function createChart() {
    const ctx = document.getElementById('priceChart').getContext('2d');
    
    const filteredData = getFilteredData(currentRange);
    
    const sortedData = filteredData.sort((a, b) => 
        new Date(a.price_check_date) - new Date(b.price_check_date)
    );
    
    const labels = sortedData.map(d => formatDate(d.price_check_date));
    const bestPrices = sortedData.map(d => parseInt(d.best_price));
    const initialPrices = sortedData.map(d => parseInt(d.initial_price));
    
    if (chart) {
        chart.destroy();
    }
    
    chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Best Price',
                    data: bestPrices,
                    borderColor: '#4F46E5',
                    backgroundColor: 'rgba(79, 70, 229, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    pointBackgroundColor: '#4F46E5',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                },
                {
                    label: 'Initial Price',
                    data: initialPrices,
                    borderColor: '#E5E7EB',
                    backgroundColor: 'rgba(229, 231, 235, 0.1)',
                    borderWidth: 2,
                    fill: false,
                    tension: 0.4,
                    pointRadius: 0,
                    pointHoverRadius: 4,
                    borderDash: [5, 5],
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index',
            },
            plugins: {
                legend: {
                    display: false,
                },
                tooltip: {
                    backgroundColor: '#1F2937',
                    titleColor: '#F9FAFB',
                    bodyColor: '#F9FAFB',
                    borderColor: '#374151',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: true,
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${maskPrice(context.parsed.y)}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    grid: {
                        color: '#F3F4F6',
                    },
                    ticks: {
                        callback: function(value) {
                            return maskPrice(value);
                        },
                        color: '#6B7280',
                        font: {
                            size: 12,
                        }
                    }
                },
                x: {
                    grid: {
                        display: false,
                    },
                    ticks: {
                        color: '#6B7280',
                        font: {
                            size: 12,
                        },
                        maxRotation: 45,
                        minRotation: 45,
                    }
                }
            }
        }
    });
}

function getFilteredData(days) {
    if (days === 'all') return priceData;
    
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - days);
    
    return priceData.filter(d => new Date(d.price_check_date) >= cutoffDate);
}

function setupEventListeners() {
    document.querySelectorAll('.btn-control').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.btn-control').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            
            const range = e.target.dataset.range;
            currentRange = range === 'all' ? 'all' : parseInt(range);
            createChart();
        });
    });
}

function downloadCSV() {
    const csvContent = convertToCSV(priceData);
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `resort_prices_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

function convertToCSV(data) {
    const headers = Object.keys(data[0]).join(',');
    const rows = data.map(row => Object.values(row).join(','));
    return [headers, ...rows].join('\n');
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric', 
        year: 'numeric' 
    });
}
