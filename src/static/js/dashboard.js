document.addEventListener('DOMContentLoaded', function() {
    
    // Verifica se o elemento do gráfico existe antes de tentar criar
    const canvasSales = document.getElementById('salesChart');
    const canvasCategory = document.getElementById('categoryChart');

    if (canvasSales) {
        const ctxSales = canvasSales.getContext('2d');
        const gradient = ctxSales.createLinearGradient(0, 0, 0, 400);
        gradient.addColorStop(0, 'rgba(30, 58, 138, 0.2)');
        gradient.addColorStop(1, 'rgba(30, 58, 138, 0)');

        new Chart(ctxSales, {
            type: 'line',
            data: {
                labels: ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun'],
                datasets: [{
                    label: 'Movimentações',
                    data: [12, 19, 15, 25, 22, 30],
                    borderColor: '#0a192f',
                    backgroundColor: gradient,
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true,
                    pointBackgroundColor: '#ffffff',
                    pointBorderColor: '#0a192f',
                    pointRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true, grid: { borderDash: [2, 4], color: '#e2e8f0' } },
                    x: { grid: { display: false } }
                }
            }
        });
    }

    if (canvasCategory) {
        const ctxCategory = canvasCategory.getContext('2d');
        new Chart(ctxCategory, {
            type: 'doughnut',
            data: {
                labels: ['Tintas', 'Solventes', 'Outros'],
                datasets: [{
                    data: [45, 30, 25],
                    backgroundColor: ['#0a192f', '#3b82f6', '#facc15'],
                    borderWidth: 0,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '70%',
                plugins: { legend: { display: false } }
            }
        });
    }
});