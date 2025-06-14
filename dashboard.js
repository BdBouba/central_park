const machines = {};
const charts = {};
const maxPoints = 30;
const ws = new WebSocket("ws://localhost:6789");

ws.onopen = () => {
    ws.send(JSON.stringify({ type: "dashboard" }));
};

function getStatusBadge(value) {
    if (value < 50) return `<span class="badge ok">OK</span>`;
    if (value < 80) return `<span class="badge warn">Élevé</span>`;
    return `<span class="badge crit">Critique</span>`;
}

function updateChart(chart, value) {
    const now = new Date().toLocaleTimeString();
    if (chart.data.labels.length >= maxPoints) {
        chart.data.labels.shift();
        chart.data.datasets[0].data.shift();
    }
    chart.data.labels.push(now);
    chart.data.datasets[0].data.push(value);
    chart.update('none');
}

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
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

        charts[`cpu-${id}`] = createChart(`cpuChart-${id}`, 'CPU (%)', 'rgba(0, 123, 255, 0.6)');
        charts[`ram-${id}`] = createChart(`ramChart-${id}`, 'RAM (%)', 'rgba(40, 167, 69, 0.6)');
        charts[`disk-${id}`] = createChart(`diskChart-${id}`, 'DISK (%)', 'rgba(255, 193, 7, 0.6)');
    }

    const block = machines[id];

    block.querySelector('.cpu').innerHTML = `${data.cpu_total}% ${getStatusBadge(data.cpu_total)}`;
    block.querySelector('.ram').innerHTML = `${data.memory_percent}% ${getStatusBadge(data.memory_percent)}`;
    block.querySelector('.disk').innerHTML = `${data.disk_percent}% ${getStatusBadge(data.disk_percent)}`;
    block.querySelector('.swap').innerHTML = `${data.swap_percent}% ${getStatusBadge(data.swap_percent)}`;
    block.querySelector('.network').innerHTML = `${(data.bytes_recv / 1024 / 1024).toFixed(1)} Mo ↓ / ${(data.bytes_sent / 1024 / 1024).toFixed(1)} Mo ↑`;
    block.querySelector('.proc').innerHTML = `${data.process_count}`;
    block.querySelector('.time').innerHTML = new Date(data.timestamp * 1000).toLocaleTimeString();

    updateChart(charts[`cpu-${id}`], data.cpu_total);
    updateChart(charts[`ram-${id}`], data.memory_percent);
    updateChart(charts[`disk-${id}`], data.disk_percent);
};

function createChart(id, label, color) {
    const ctx = document.getElementById(id).getContext('2d');
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label,
                data: [],
                borderColor: color,
                backgroundColor: color.replace('0.6', '0.2'),
                fill: true,
                tension: 0.4,
            }]
        },
        options: {
            responsive: true,
            animation: false,
            scales: {
                y: {
                    min: 0,
                    max: 100,
                    ticks: { stepSize: 20 }
                }
            },
            plugins: {
                legend: { display: true }
            }
        }
    });
}
document.addEventListener('DOMContentLoaded', () => {
    const machinesContainer = document.getElementById('machines');
    if (!machinesContainer) {
        console.error("L'élément 'machines' n'a pas été trouvé dans le DOM.");
    }
});
