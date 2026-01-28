// src/static/js/dashboard.js

document.addEventListener('DOMContentLoaded', function() {
    
    // 1. CARREGAR DADOS DOS GRÁFICOS
    let dados = {
        chartLabels: [],
        chartVendas: [],
        chartDespesas: [],
        doughLabels: [],
        doughData: [],
        metaPerc: 0
    };

    const elementoDados = document.getElementById('kpi-data');
    if (elementoDados) {
        try {
            dados = JSON.parse(elementoDados.textContent);
        } catch (e) {
            console.error('Erro ao ler dados do Dashboard:', e);
        }
    }

    // 2. GRÁFICOS CHART.JS
    const canvasFin = document.getElementById('financeiroChart');
    if (canvasFin) {
        const ctx = canvasFin.getContext('2d');
        const gradVendas = ctx.createLinearGradient(0, 0, 0, 400);
        gradVendas.addColorStop(0, 'rgba(34, 197, 94, 0.2)'); 
        gradVendas.addColorStop(1, 'rgba(34, 197, 94, 0)');

        const gradDespesas = ctx.createLinearGradient(0, 0, 0, 400);
        gradDespesas.addColorStop(0, 'rgba(239, 68, 68, 0.2)'); 
        gradDespesas.addColorStop(1, 'rgba(239, 68, 68, 0)');

        new Chart(ctx, {
            type: 'line',
            data: {
                labels: dados.chartLabels,
                datasets: [
                    {
                        label: 'Receitas (R$)',
                        data: dados.chartVendas,
                        borderColor: '#22c55e',
                        backgroundColor: gradVendas,
                        borderWidth: 2,
                        tension: 0.4,
                        fill: true,
                        pointBackgroundColor: '#ffffff',
                        pointBorderColor: '#22c55e',
                        pointRadius: 4
                    },
                    {
                        label: 'Despesas (R$)',
                        data: dados.chartDespesas,
                        borderColor: '#ef4444',
                        backgroundColor: gradDespesas,
                        borderWidth: 2,
                        tension: 0.4,
                        fill: true,
                        pointBackgroundColor: '#ffffff',
                        pointBorderColor: '#ef4444',
                        pointRadius: 4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'top' } },
                scales: {
                    y: { beginAtZero: true, grid: { borderDash: [2, 4], color: '#e2e8f0' } },
                    x: { grid: { display: false } }
                }
            }
        });
    }

    const canvasCat = document.getElementById('categoriaChart');
    if (canvasCat) {
        const ctxCat = canvasCat.getContext('2d');
        const palette = ['#0a192f', '#3b82f6', '#facc15', '#ef4444', '#10b981', '#8b5cf6', '#f97316'];

        new Chart(ctxCat, {
            type: 'doughnut',
            data: {
                labels: dados.doughLabels,
                datasets: [{
                    data: dados.doughData,
                    backgroundColor: palette,
                    borderWidth: 0,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '70%',
                plugins: { legend: { position: 'right', labels: { boxWidth: 12, font: { size: 11 } } } }
            }
        });
    }
});

// 3. FUNÇÕES GLOBAIS DE MODAL (Necessárias para o onclick)
window.abrirModal = function(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        const content = modal.querySelector('div');
        modal.classList.remove('hidden');
        setTimeout(() => {
            modal.classList.remove('opacity-0');
            if(content) {
                content.classList.remove('scale-95');
                content.classList.add('scale-100');
            }
        }, 10);
    }
}

window.fecharModal = function(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        const content = modal.querySelector('div');
        modal.classList.add('opacity-0');
        if(content) {
            content.classList.remove('scale-100');
            content.classList.add('scale-95');
        }
        setTimeout(() => {
            modal.classList.add('hidden');
        }, 300);
    }
}

// Fechar com ESC ou Clicar Fora
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal-overlay:not(.hidden)').forEach(m => fecharModal(m.id));
    }
});

document.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal-overlay')) {
        fecharModal(e.target.id);
    }
});