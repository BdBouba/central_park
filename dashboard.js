const machines = {};
const charts = {};
const maxValues = {};
const avgValues = {};
const maxPoints = 30;
const ws = new WebSocket("ws://localhost:6789");

ws.onopen = () => {
    ws.send(JSON.stringify({ type: "dashboard" }));
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);

    // Handle server metrics (only imperative performance and server stats)
    if (data.type === "server") {
        const serverMetrics = data.metrics;

        // Display server metrics (e.g., CPU, RAM, Disk, etc.)
        document.getElementById('server-cpu').textContent = `${serverMetrics.cpu_percent}% CPU`;
        document.getElementById('server-ram').textContent = `${serverMetrics.memory_percent}% RAM`;
        document.getElementById('server-disk').textContent = `${serverMetrics.disk_percent}% Disk`;

        // Display only imperative performance time
        document.getElementById('imperative-time').textContent = `Imperative Time: ${serverMetrics.imperative_time.toFixed(2)}s`;

    } else if (data.type === "client") {
        // Handle client data
        const id = data.identifier;
        if (!machines[id]) {
            const block = document.createElement('div');
            block.className = 'machine';
            block.id = `machine-${id}`;
            block.innerHTML = `
                <h2>🖥 Machine ${id}</h2>
                <div class="stats">
                    <p><strong>CPU:</strong> <span class="cpu"></span></p>
                    <p><strong>RAM:</strong> <span class="ram"></span></p>
                    <p><strong>DISK:</strong> <span class="disk"></span></p>
                    <p><strong>SWAP:</strong> <span class="swap"></span></p>
                    <p><strong>Réseau:</strong> <span class="network"></span></p>
                    <p><strong>Processus:</strong> <span class="proc"></span></p>
                    <p><strong>MAJ:</strong> <span class="time"></span></p>
                </div>
                <canvas id="cpuChart-${id}"></canvas>
                <canvas id="ramChart-${id}"></canvas>
                <canvas id="diskChart-${id}"></canvas>
            `;
            document.getElementById('machines').appendChild(block);
            machines[id] = block;

            // Create charts for each client machine
            charts[`cpu-${id}`] = createChart(`cpuChart-${id}`, 'CPU (%)', 'rgba(0, 123, 255, 0.6)');
            charts[`ram-${id}`] = createChart(`ramChart-${id}`, 'RAM (%)', 'rgba(40, 167, 69, 0.6)');
            charts[`disk-${id}`] = createChart(`diskChart-${id}`, 'DISK (%)', 'rgba(255, 193, 7, 0.6)');
        }

        // Update the machine data in the dashboard
        machines[id].querySelector('.cpu').innerHTML = `${data.cpu_total}%`;
        machines[id].querySelector('.ram').innerHTML = `${data.memory_percent}%`;
        machines[id].querySelector('.disk').innerHTML = `${data.disk_percent}%`;
        machines[id].querySelector('.swap').innerHTML = `${data.swap_percent !== null ? data.swap_percent : 'N/A'}%`;
        machines[id].querySelector('.network').innerHTML = `${(data.bytes_sent / 1024).toFixed(2)} KB Sent | ${(data.bytes_recv / 1024).toFixed(2)} KB Received`;
        machines[id].querySelector('.proc').innerHTML = `${data.process_count} Processes`;
        machines[id].querySelector('.time').innerHTML = new Date(data.timestamp * 1000).toLocaleString();

        // Update the charts with the latest values
        updateChart(charts[`cpu-${id}`], data.cpu_total);
        updateChart(charts[`ram-${id}`], data.memory_percent);
        updateChart(charts[`disk-${id}`], data.disk_percent);
    }
};

// Helper function to create a chart
function createChart(elementId, label, borderColor) {
    return new Chart(document.getElementById(elementId), {
        type: 'line',
        data: {
            labels: Array.from({ length: maxPoints }, (_, i) => i + 1),
            datasets: [{
                label: label,
                backgroundColor: 'rgba(0, 0, 0, 0.1)',
                borderColor: borderColor,
                data: Array(maxPoints).fill(0),
                fill: false,
                borderWidth: 2,
                lineTension: 0.1
            }]
        },
        options: {
            responsive: true,
            scales: {
                x: {
                    ticks: {
                        autoSkip: true,
                        maxTicksLimit: maxPoints
                    }
                },
                y: {
                    beginAtZero: true,
                    max: 100
                }
            }
        }
    });
}

// Helper function to update the chart data
function updateChart(chart, value) {
    chart.data.datasets[0].data.push(value);
    if (chart.data.datasets[0].data.length > maxPoints) {
        chart.data.datasets[0].data.shift();
    }
    chart.update();
}

// Event listener for closing WebSocket connection
ws.onclose = () => {
    console.log("WebSocket connection closed");
};

// Handle WebSocket errors
ws.onerror = (error) => {
    console.error("WebSocket error: ", error);
};
