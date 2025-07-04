// Color scheme for different types
const typeColors = {
    'Chinese': '#FF6B6B',
    'Maths': '#4ECDC4',
    'English': '#45B7D1',
    'Physics': '#96CEB4',
    'Chemistry': '#FFEAA7',
    'Biology': '#DDA0DD',
    'Programming': '#74B9FF',
    'Default': '#95A5A6'
};

let yamlData = [];
let pieChart = null;
let lineChart = null;

// File input handler
document.getElementById('fileInput').addEventListener('change', handleFileSelect);

function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            try {
                const yamlContent = e.target.result;
                yamlData = jsyaml.load(yamlContent);
                processData();
            } catch (error) {
                alert('Error parsing YAML file: ' + error.message);
            }
        };
        reader.readAsText(file);
    }
}

// Load sample data for demonstration
function loadSampleData() {
    yamlData = [
        {
            duration: 951.523,
            end: '2025-06-30T17:53:36.435',
            name: '1-1',
            start: '2025-06-30T17:37:44.912',
            tag: 'Online Course',
            type: 'Biology'
        },
        {
            duration: 1200.5,
            end: '2025-06-30T14:30:00.000',
            name: '2-1',
            start: '2025-06-30T14:10:00.000',
            tag: 'Homework',
            type: 'Maths'
        },
        {
            duration: 1800.0,
            end: '2025-07-01T10:30:00.000',
            name: '3-1',
            start: '2025-07-01T10:00:00.000',
            tag: 'Reading',
            type: 'English'
        },
        {
            duration: 2400.0,
            end: '2025-07-01T16:00:00.000',
            name: '4-1',
            start: '2025-07-01T15:20:00.000',
            tag: 'Lab Work',
            type: 'Physics'
        },
        {
            duration: 1500.0,
            end: '2025-07-02T06:25:00.000',
            name: '5-1',
            start: '2025-07-02T06:00:00.000',
            tag: 'Practice',
            type: 'Programming'
        }
    ];
    processData();
}

function processData() {
    if (!yamlData || yamlData.length === 0) {
        alert('No data to process');
        return;
    }

    // Process dates and times
    yamlData.forEach(item => {
        item.startDate = new Date(item.start);
        item.endDate = new Date(item.end);

        const year = item.startDate.getFullYear();
        const month = String(item.startDate.getMonth() + 1).padStart(2, '0');
        const day = String(item.startDate.getDate()).padStart(2, '0');
        item.dayKey = `${year}-${month}-${day}`;
    });

    // Sort data by start time
    yamlData.sort((a, b) => a.startDate - b.startDate);

    generateTimeline();
    generateCharts();
    generateDataDivs();
}

function generateTimeline() {
    const timelineContainer = document.getElementById('timelineContainer');
    timelineContainer.innerHTML = '';

    // Group data by day
    const dayGroups = {};
    yamlData.forEach(item => {
        if (!dayGroups[item.dayKey]) {
            dayGroups[item.dayKey] = [];
        }
        dayGroups[item.dayKey].push(item);
    });

    // Create timeline for each day
    Object.keys(dayGroups).sort().forEach(day => {
        const dayData = dayGroups[day];
        const dayDiv = document.createElement('div');
        dayDiv.className = 'timeline-day';

        const dayHeader = document.createElement('h3');
        dayHeader.textContent = new Date(day + 'T00:00:00Z').toLocaleDateString('en-US', {
            timeZone: 'UTC',
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
        dayDiv.appendChild(dayHeader);

        // Find day bounds
        const dayStart = new Date(day + 'T00:00:00');
        const dayDurationMs = 24 * 60 * 60 * 1000;

        // Create timeline bar
        const timelineBar = document.createElement('div');
        timelineBar.className = 'timeline-bar';

        dayData.forEach(item => {
            const itemDiv = document.createElement('div');
            itemDiv.className = 'timeline-item';

            const startOffset = (item.startDate - dayStart) / dayDurationMs * 100;
            const itemWidth = (item.duration * 1000) / dayDurationMs * 100;
            if (startOffset < 0) return;
            itemDiv.style.left = startOffset + '%';
            itemDiv.style.width = itemWidth + '%';
            itemDiv.style.backgroundColor = typeColors[item.type] || typeColors['Default'];
            itemDiv.textContent = item.name;
            itemDiv.title = `${item.name} (${item.type}) - ${formatDuration(item.duration)}`;
            
            timelineBar.appendChild(itemDiv);
        });

        dayDiv.appendChild(timelineBar);

        // Create legend
        const legend = document.createElement('div');
        legend.className = 'timeline-legend';

        const usedTypes = [...new Set(dayData.map(item => item.type))];
        usedTypes.forEach(type => {
            const legendItem = document.createElement('div');
            legendItem.className = 'legend-item';

            const colorBox = document.createElement('div');
            colorBox.className = 'legend-color';
            colorBox.style.backgroundColor = typeColors[type] || typeColors['Default'];

            const label = document.createElement('span');
            label.textContent = type;

            legendItem.appendChild(colorBox);
            legendItem.appendChild(label);
            legend.appendChild(legendItem);
        });

        dayDiv.appendChild(legend);
        timelineContainer.appendChild(dayDiv);
    });
}

function generateCharts() {
    generatePieChart();
    generateLineChart();
}

function generatePieChart() {
    const ctx = document.getElementById('pieChart').getContext('2d');

    // Calculate total duration by type
    const typeDurations = {};
    yamlData.forEach(item => {
        if (!typeDurations[item.type]) {
            typeDurations[item.type] = 0;
        }
        typeDurations[item.type] += item.duration;
    });

    const types = Object.keys(typeDurations);
    const durations = types.map(type => typeDurations[type]);
    const colors = types.map(type => typeColors[type] || typeColors['Default']);

    if (pieChart) {
        pieChart.destroy();
    }

    pieChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: types,
            datasets: [{
                data: durations,
                backgroundColor: colors,
                borderColor: '#fff',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom',
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${label}: ${formatDuration(value)} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

function generateLineChart() {
    const ctx = document.getElementById('lineChart').getContext('2d');

    // Calculate daily totals
    const dailyTotals = {};
    yamlData.forEach(item => {
        if (!dailyTotals[item.dayKey]) {
            dailyTotals[item.dayKey] = 0;
        }
        dailyTotals[item.dayKey] += item.duration;
    });

    const dates = Object.keys(dailyTotals).sort();
    const totals = dates.map(date => dailyTotals[date] / 3600); // Convert to hours

    if (lineChart) {
        lineChart.destroy();
    }

    lineChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates.map(date => new Date(date + 'T00:00:00Z').toLocaleDateString('en-US', {
                timeZone: 'UTC'
            })),
            datasets: [{
                label: 'Daily Total (hours)',
                data: totals,
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#667eea',
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: 6
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Hours'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Date'
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

function generateDataDivs() {
    const dataContainer = document.getElementById('dataContainer');
    dataContainer.innerHTML = '';

    // Group by type
    const typeGroups = {};
    yamlData.forEach(item => {
        if (!typeGroups[item.type]) {
            typeGroups[item.type] = {};
        }
        if (!typeGroups[item.type][item.tag]) {
            typeGroups[item.type][item.tag] = [];
        }
        typeGroups[item.type][item.tag].push(item);
    });

    // Create divs for each type
    Object.keys(typeGroups).sort().forEach(type => {
        const typeDiv = document.createElement('div');
        typeDiv.className = 'type-group';

        const typeHeader = document.createElement('div');
        typeHeader.className = 'type-header';
        typeHeader.textContent = type;
        typeDiv.appendChild(typeHeader);

        // Create divs for each tag within the type
        Object.keys(typeGroups[type]).sort().forEach(tag => {
            const tagDiv = document.createElement('div');
            tagDiv.className = 'tag-group';

            const tagHeader = document.createElement('div');
            tagHeader.className = 'tag-header';
            tagHeader.textContent = tag;
            tagDiv.appendChild(tagHeader);

            // Sort items by start time
            const sortedItems = typeGroups[type][tag].sort((a, b) => a.startDate - b.startDate);

            sortedItems.forEach(item => {
                const itemDiv = document.createElement('div');
                itemDiv.className = 'data-item';

                const itemHeader = document.createElement('div');
                itemHeader.className = 'data-item-header';

                const itemName = document.createElement('div');
                itemName.className = 'data-item-name';
                itemName.textContent = item.name;

                const itemDuration = document.createElement('div');
                itemDuration.className = 'data-item-duration';
                itemDuration.textContent = formatDuration(item.duration);

                itemHeader.appendChild(itemName);
                itemHeader.appendChild(itemDuration);

                const itemDetails = document.createElement('div');
                itemDetails.className = 'data-item-details';

                const itemDate = document.createElement('div');
                itemDate.textContent = `📅 ${item.startDate.toLocaleDateString()}`;

                const itemTime = document.createElement('div');
                itemTime.className = 'data-item-time';
                itemTime.textContent = `🕒 ${item.startDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} - ${item.endDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;

                itemDetails.appendChild(itemDate);
                itemDetails.appendChild(itemTime);

                itemDiv.appendChild(itemHeader);
                itemDiv.appendChild(itemDetails);

                tagDiv.appendChild(itemDiv);
            });

            typeDiv.appendChild(tagDiv);
        });

        dataContainer.appendChild(typeDiv);
    });
}

function formatDuration(seconds) {
    if (isNaN(seconds) || seconds < 0) return '0s';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const remainingSeconds = Math.floor(seconds % 60);

    let parts = [];
    if (hours > 0) parts.push(`${hours}h`);
    if (minutes > 0) parts.push(`${minutes}m`);
    if (remainingSeconds > 0 || parts.length === 0) parts.push(`${remainingSeconds}s`);

    return parts.join(' ');
}

// Initialize with sample data on page load
document.addEventListener('DOMContentLoaded', function() {
    // You can uncomment the next line to load sample data automatically
    // loadSampleData();
});
