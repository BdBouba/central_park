const machines = {};
const charts = {};
const maxValues = {};
const avgValues = {};
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

function updateChart(chart, value, peak, avg) {
    const now = new Date().toLocaleTimeString();
    if (chart.data.labels.length >= maxPoints) {
        chart.data.labels.shift();
        chart.data.datasets[0].data.shift();
    }
    chart.data.labels.push(now);
    chart.data.datasets[0].data.push(value);

    chart.options.plugins.annotation.annotations.peak.yMin = peak;
    chart.options.plugins.annotation.annotations.peak.yMax = peak;

    chart.options.plugins.annotation.annotations.average.yMin = avg;
    chart.options.plugins.annotation.annotations.average.yMax = avg;

    chart.update('none');
}

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
                tension: 0.4
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
                legend: { display: true },
                annotation: {
                    annotations: {
                        peak: {
                            type: 'line',
                            yMin: 0,
                            yMax: 0,
                            borderColor: 'red',
                            borderWidth: 1,
                            borderDash: [5, 5],
                            label: {
                                enabled: true,
                                content: 'Peak',
                                position: 'end'
                            }
                        },
                        average: {
                            type: 'line',
                            yMin: 0,
                            yMax: 0,
                            borderColor: 'blue',
                            borderWidth: 1,
                            borderDash: [4, 4],
                            label: {
                                enabled: true,
                                content: 'Avg',
                                position: 'start'
                            }
                        }
                    }
                }
            }
        }
    });
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

        maxValues[id] = { cpu: 0, ram: 0, disk: 0, swap: 0 };
        avgValues[id] = {
            cpu: { sum: 0, count: 0 },
            ram: { sum: 0, count: 0 },
            disk: { sum: 0, count: 0 },
            swap: { sum: 0, count: 0 }
        };
    }

    // MAJ des valeurs max
    maxValues[id].cpu = Math.max(maxValues[id].cpu, data.cpu_total);
    maxValues[id].ram = Math.max(maxValues[id].ram, data.memory_percent);
    maxValues[id].disk = Math.max(maxValues[id].disk, data.disk_percent);
    maxValues[id].swap = Math.max(maxValues[id].swap, data.swap_percent);

    // Moyennes
    const avg = avgValues[id];
    avg.cpu.sum += data.cpu_total; avg.cpu.count++;
    avg.ram.sum += data.memory_percent; avg.ram.count++;
    avg.disk.sum += data.disk_percent; avg.disk.count++;
    avg.swap.sum += data.swap_percent; avg.swap.count++;

    const avgDisplay = {
        cpu: (avg.cpu.sum / avg.cpu.count).toFixed(1),
        ram: (avg.ram.sum / avg.ram.count).toFixed(1),
        disk: (avg.disk.sum / avg.disk.count).toFixed(1),
        swap: (avg.swap.sum / avg.swap.count).toFixed(1)
    };

    // Barres + valeurs
    machines[id].querySelector('.cpu').innerHTML = `
        ${data.cpu_total}% ${getStatusBadge(data.cpu_total)} (Avg: ${avgDisplay.cpu}%, Peak: ${maxValues[id].cpu}%)
        <div class="bar-container"><div class="bar cpu" style="width:${data.cpu_total}%;"></div></div>`;

    machines[id].querySelector('.ram').innerHTML = `
        ${data.memory_percent}% ${getStatusBadge(data.memory_percent)} (Avg: ${avgDisplay.ram}%, Peak: ${maxValues[id].ram}%)
        <div class="bar-container"><div class="bar ram" style="width:${data.memory_percent}%;"></div></div>`;

    machines[id].querySelector('.disk').innerHTML = `
        ${data.disk_percent}% ${getStatusBadge(data.disk_percent)} (Avg: ${avgDisplay.disk}%, Peak: ${maxValues[id].disk}%)
        <div class="bar-container"><div class="bar disk" style="width:${data.disk_percent}%;"></div></div>`;

    machines[id].querySelector('.swap').innerHTML = `
        ${data.swap_percent}% ${getStatusBadge(data.swap_percent)} (Avg: ${avgDisplay.swap}%, Peak: ${maxValues[id].swap}%)
        <div class="bar-container"><div class="bar swap" style="width:${data.swap_percent}%;"></div></div>`;

    machines[id].querySelector('.network').innerHTML =
        `${(data.bytes_recv / 1024 / 1024).toFixed(1)} Mo ↓ / ${(data.bytes_sent / 1024 / 1024).toFixed(1)} Mo ↑`;

    machines[id].querySelector('.proc').innerHTML = `${data.process_count}`;
    machines[id].querySelector('.time').innerHTML = new Date(data.timestamp * 1000).toLocaleTimeString();

    // MAJ des graphiques
    updateChart(charts[`cpu-${id}`], data.cpu_total, maxValues[id].cpu, avgDisplay.cpu);
    updateChart(charts[`ram-${id}`], data.memory_percent, maxValues[id].ram, avgDisplay.ram);
    updateChart(charts[`disk-${id}`], data.disk_percent, maxValues[id].disk, avgDisplay.disk);
};

document.addEventListener('DOMContentLoaded', () => {
    const machinesContainer = document.getElementById('machines');
    if (!machinesContainer) {
        console.error("L'élément 'machines' n'a pas été trouvé dans le DOM.");
    }
});
