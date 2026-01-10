// Configuration - UPDATE THIS WITH YOUR S3 BUCKET URL
const CONFIG = {
    // Replace with your S3 bucket URL after deployment
    csvUrl: 'https://YOUR-BUCKET-NAME.s3.amazonaws.com/price_history.csv',
    // Or use CloudFront URL for better performance:
    // csvUrl: 'https://YOUR-CLOUDFRONT-DOMAIN.cloudfront.net/price_history.csv',
};

let priceData = [];
let chart = null;
let currentRange = 30;

// Initialize the app
document.addEventListener('DOMContentLoaded', async () => {
    await loadPriceData();
    setupEventListeners();
});

// Fetch CSV data from S3
async function loadPriceData() {
    const loadingOverlay = document.getElementById('loadingOverlay');
    
    try {
        // Add timestamp to prevent caching (cache-busting)
        const cacheBuster = `?t=${Date.now()}`;
        const response = await fetch(CONFIG.csvUrl + cacheBuster, {
            cache: 'no-store',  // Tell browser not to cache
            headers: {
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache'
            }
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const csvText = await response.text();
        priceData = parseCSV(csvText);
        
        // Update UI
        updateStats();
        createChart();
        populateTable();
        
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
                <p style="color: #6B7280; margin-bottom: 16px;">Could not fetch price history from S3</p>
                <button onclick="location.reload()" style="padding: 10px 20px; background: #4F46E5; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: 600;">
                    Retry
                </button>
            </div>
        `;
    }
}

// Parse CSV text into array of objects
function parseCSV(csvText) {
    const lines = csvText.trim().split('\n');
    const headers = lines[0].split(',');
    
    return lines.slice(1).map(line => {
        const values = line.split(',');
        const row = {};
        headers.forEach((header, index) => {
            row[header.trim()] = values[index]?.trim() || '';
        });
        return row;
    }).filter(row => row.price_check_date); // Filter out empty rows
}

// Update statistics cards
function updateStats() {
    if (priceData.length === 0) return;
    
    // Sort by date (most recent first)
    const sortedData = [...priceData].sort((a, b) => 
        new Date(b.price_check_date) - new Date(a.price_check_date)
    );
    
    const latest = sortedData[0];
    const previous = sortedData[1];
    
    // Current Price
    const currentPrice = parseInt(latest.best_price);
    document.getElementById('currentPrice').textContent = `$${currentPrice.toLocaleString()}`;
    
    // Price Change
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
    
    // Lowest Price
    const lowestEntry = priceData.reduce((min, entry) => 
        parseInt(entry.best_price) < parseInt(min.best_price) ? entry : min
    );
    document.getElementById('lowestPrice').textContent = `$${parseInt(lowestEntry.best_price).toLocaleString()}`;
    document.getElementById('lowestDate').textContent = formatDate(lowestEntry.price_check_date);
    
    // Trend (last 30 days)
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
    
    // Last Update
    document.getElementById('lastUpdate').textContent = formatDate(latest.price_check_date);
}

// Create price chart
function createChart() {
    const ctx = document.getElementById('priceChart').getContext('2d');
    
    // Filter data based on selected range
    const filteredData = getFilteredData(currentRange);
    
    // Sort by date (oldest first for chart)
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
                            return `${context.dataset.label}: $${context.parsed.y.toLocaleString()}`;
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
                            return '$' + value.toLocaleString();
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

// Populate data table
function populateTable() {
    const tbody = document.getElementById('tableBody');
    
    // Sort by date (most recent first)
    const sortedData = [...priceData].sort((a, b) => 
        new Date(b.price_check_date) - new Date(a.price_check_date)
    );
    
    tbody.innerHTML = sortedData.map(row => {
        const bestPrice = parseInt(row.best_price);
        const initialPrice = parseInt(row.initial_price);
        const savings = initialPrice - bestPrice;
        const discount = ((savings / initialPrice) * 100).toFixed(0);
        
        return `
            <tr>
                <td>${formatDate(row.price_check_date)}</td>
                <td class="price-cell">$${bestPrice.toLocaleString()}</td>
                <td>$${initialPrice.toLocaleString()}</td>
                <td class="savings-cell">$${savings.toLocaleString()}</td>
                <td><span class="discount-badge">${discount}% OFF</span></td>
            </tr>
        `;
    }).join('');
}

// Get filtered data based on range
function getFilteredData(days) {
    if (days === 'all') return priceData;
    
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - days);
    
    return priceData.filter(d => new Date(d.price_check_date) >= cutoffDate);
}

// Setup event listeners
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

// Download CSV
function downloadCSV() {
    const csvContent = convertToCSV(priceData);
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `club_med_prices_${new Date().toISOString().split('T')[0]}.csv`;
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

// Format date for display
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric', 
        year: 'numeric' 
    });
}
