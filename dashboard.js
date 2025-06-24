const machines = {};
const charts = {};
const maxPoints = 30;

function fetchServerMetrics() {
    fetch("http://localhost:5000/metrics")
        .then(response => response.json())
        .then(data => {
            const serverMetrics = data.metrics;

            document.getElementById('server-cpu').textContent = `${serverMetrics.cpu_percent}% CPU (Total: ${serverMetrics.cpu_total} cores)`;
            document.getElementById('server-ram').textContent = `${serverMetrics.memory_usage.toFixed(2)} MB RAM (Total: ${serverMetrics.memory_total.toFixed(2)} MB)`;
            document.getElementById('imperative-time').textContent = `Imperative Time: ${serverMetrics.imperative_time.toFixed(2)}s`;
        })
        .catch(error => console.error("Error fetching server metrics:", error));
}

function fetchClients() {
    fetch("http://localhost:5000/clients")
        .then(res => res.json())
        .then(data => {
            if (data.type === "clients") {
                data.data.forEach(updateClientDisplay);
            }
        })
        .catch(err => console.error("Error fetching client data:", err));
}

function updateClientDisplay(data) {
    const id = data.identifier;

    if (!machines[id]) {
        const block = document.createElement('div');
        block.className = 'machine';
        block.id = `machine-${id}`;
        block.innerHTML = `
            <h2>🖥 Machine ${id}</h2>
            <div class="stats">
                <p><strong>CPU:</strong> <span class="cpu">Loading...</span></p>
                <p><strong>RAM:</strong> <span class="ram">Loading...</span></p>
                <p><strong>SWAP:</strong> <span class="swap">Loading...</span></p>
                <p><strong>Réseau:</strong> <span class="network">Loading...</span></p>
                <p><strong>Processus:</strong> <span class="proc">Loading...</span></p>
                <p><strong>MAJ:</strong> <span class="time">Loading...</span></p>
            </div>
            <canvas id="cpuChart-${id}"></canvas>
            <canvas id="ramChart-${id}"></canvas>
        `;
        document.getElementById('machines').appendChild(block);
        machines[id] = block;

        charts[`cpu-${id}`] = createChart(`cpuChart-${id}`, 'CPU (%)', 'rgba(0, 123, 255, 0.6)');
        charts[`ram-${id}`] = createChart(`ramChart-${id}`, 'RAM (%)', 'rgba(40, 167, 69, 0.6)');
    }

    machines[id].querySelector('.cpu').innerHTML = `${data.cpu_percent || 'N/A'}% | ${data.cpu_total ? data.cpu_total.toFixed(2) : 'N/A'} cores`;
    machines[id].querySelector('.ram').innerHTML = `${data.memory_percent || 'N/A'}% | ${data.memory_usage ? data.memory_usage.toFixed(2) : 'N/A'} MB`;
    machines[id].querySelector('.swap').innerHTML = `${data.swap_percent !== null ? data.swap_percent : 'N/A'}% | ${data.swap_usage ? data.swap_usage.toFixed(2) : 'N/A'} MB`;
    machines[id].querySelector('.network').innerHTML = `${(data.bytes_sent / 1024).toFixed(2)} KB Sent | ${(data.bytes_recv / 1024).toFixed(2)} KB Received`;
    machines[id].querySelector('.proc').innerHTML = `${data.process_count} Processes`;
    machines[id].querySelector('.time').innerHTML = new Date(data.timestamp * 1000).toLocaleString();

    updateChart(charts[`cpu-${id}`], data.cpu_percent);
    updateChart(charts[`ram-${id}`], data.memory_percent);
}

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

function updateChart(chart, value) {
    chart.data.datasets[0].data.push(value);
    if (chart.data.datasets[0].data.length > maxPoints) {
        chart.data.datasets[0].data.shift();
    }
    chart.update();
}

setInterval(fetchServerMetrics, 1000);
setInterval(fetchClients, 1000);
