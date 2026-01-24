// Funções de Modal Globais
function abrirModal(modalId) {
    const modal = document.getElementById(modalId);
    const modalContent = modal.querySelector('div'); // O container branco dentro do modal
    
    if (modal) {
        modal.classList.remove('hidden');
        // Pequeno delay para permitir a animação CSS
        setTimeout(() => {
            modal.classList.remove('opacity-0');
            if (modalContent) {
                modalContent.classList.remove('scale-95');
                modalContent.classList.add('scale-100');
            }
        }, 10);
    }
}

function fecharModal(modalId) {
    const modal = document.getElementById(modalId);
    const modalContent = modal.querySelector('div');
    
    if (modal) {
        modal.classList.add('opacity-0');
        if (modalContent) {
            modalContent.classList.remove('scale-100');
            modalContent.classList.add('scale-95');
        }
        // Espera a animação acabar para esconder
        setTimeout(() => {
            modal.classList.add('hidden');
        }, 300);
    }
}

// Fechar ao clicar fora
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal-overlay')) {
        fecharModal(e.target.id);
    }
});

// ESC para fechar
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        const modals = document.querySelectorAll('.modal-overlay');
        modals.forEach(m => {
            if (!m.classList.contains('hidden')) {
                fecharModal(m.id);
            }
        });
    }
});

document.addEventListener('DOMContentLoaded', function() {
    
    // 1. GRÁFICO DE LINHA (Financeiro)
    const canvasFin = document.getElementById('financeiroChart');
    if (canvasFin && typeof CHART_LABELS !== 'undefined') {
        const ctx = canvasFin.getContext('2d');
        
        // Gradiente para Vendas
        const gradVendas = ctx.createLinearGradient(0, 0, 0, 400);
        gradVendas.addColorStop(0, 'rgba(34, 197, 94, 0.2)'); // Green
        gradVendas.addColorStop(1, 'rgba(34, 197, 94, 0)');

        // Gradiente para Despesas
        const gradDespesas = ctx.createLinearGradient(0, 0, 0, 400);
        gradDespesas.addColorStop(0, 'rgba(239, 68, 68, 0.2)'); // Red
        gradDespesas.addColorStop(1, 'rgba(239, 68, 68, 0)');

        new Chart(ctx, {
            type: 'line',
            data: {
                labels: CHART_LABELS,
                datasets: [
                    {
                        label: 'Receitas (R$)',
                        data: CHART_VENDAS,
                        borderColor: '#22c55e', // Green 500
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
                        data: CHART_DESPESAS,
                        borderColor: '#ef4444', // Red 500
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
                plugins: { 
                    legend: { position: 'top' },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) label += ': ';
                                if (context.parsed.y !== null) {
                                    label += new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(context.parsed.y);
                                }
                                return label;
                            }
                        }
                    }
                },
                scales: {
                    y: { 
                        beginAtZero: true, 
                        grid: { borderDash: [2, 4], color: '#e2e8f0' },
                        ticks: {
                            callback: function(value) {
                                return 'R$ ' + value / 1000 + 'k'; // Formato curto
                            }
                        }
                    },
                    x: { grid: { display: false } }
                }
            }
        });
    }

    // 2. GRÁFICO DE ROSCA (Categorias)
    const canvasCat = document.getElementById('categoriaChart');
    if (canvasCat && typeof DOUGH_LABELS !== 'undefined') {
        const ctxCat = canvasCat.getContext('2d');
        
        // Cores padrão do Eletromaster + Auxiliares
        const palette = ['#0a192f', '#3b82f6', '#facc15', '#ef4444', '#10b981', '#8b5cf6', '#f97316'];

        new Chart(ctxCat, {
            type: 'doughnut',
            data: {
                labels: DOUGH_LABELS,
                datasets: [{
                    data: DOUGH_DATA,
                    backgroundColor: palette,
                    borderWidth: 0,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '70%',
                plugins: { 
                    legend: { position: 'right', labels: { boxWidth: 12, font: { size: 11 } } },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                let val = context.parsed;
                                // Se for valor monetário (assumindo que labels são categorias)
                                if (val > 100) { 
                                     return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val);
                                }
                                return val;
                            }
                        }
                    }
                }
            }
        });
    }
});