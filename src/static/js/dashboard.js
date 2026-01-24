// src/static/js/dashboard.js

document.addEventListener('DOMContentLoaded', function() {
    
    // =========================================================
    // 1. RECUPERAÇÃO DOS DADOS DO HTML (JSON)
    // =========================================================
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

    // =========================================================
    // 2. BARRA DE PROGRESSO DA META
    // =========================================================
    const barra = document.getElementById('barraMeta');
    if (barra) {
        // Trava em 100% visualmente se passou da meta
        let largura = dados.metaPerc > 100 ? 100 : dados.metaPerc;
        // Pequeno delay para a animação CSS funcionar
        setTimeout(() => {
            barra.style.width = largura + '%';
        }, 100);
    }

    // =========================================================
    // 3. GRÁFICO DE LINHA (FLUXO FINANCEIRO)
    // =========================================================
    const canvasFin = document.getElementById('financeiroChart');
    if (canvasFin) {
        const ctx = canvasFin.getContext('2d');
        
        // Gradientes
        const gradVendas = ctx.createLinearGradient(0, 0, 0, 400);
        gradVendas.addColorStop(0, 'rgba(34, 197, 94, 0.2)'); // Verde transparente
        gradVendas.addColorStop(1, 'rgba(34, 197, 94, 0)');

        const gradDespesas = ctx.createLinearGradient(0, 0, 0, 400);
        gradDespesas.addColorStop(0, 'rgba(239, 68, 68, 0.2)'); // Vermelho transparente
        gradDespesas.addColorStop(1, 'rgba(239, 68, 68, 0)');

        new Chart(ctx, {
            type: 'line',
            data: {
                labels: dados.chartLabels,
                datasets: [
                    {
                        label: 'Receitas (R$)',
                        data: dados.chartVendas,
                        borderColor: '#22c55e', // Verde
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
                        borderColor: '#ef4444', // Vermelho
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
                                if(value >= 1000) return 'R$ ' + value / 1000 + 'k';
                                return 'R$ ' + value;
                            }
                        }
                    },
                    x: { grid: { display: false } }
                }
            }
        });
    }

    // =========================================================
    // 4. GRÁFICO DE ROSCA (CATEGORIAS)
    // =========================================================
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
                plugins: { 
                    legend: { position: 'right', labels: { boxWidth: 12, font: { size: 11 } } },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                let val = context.parsed;
                                let label = context.label || '';
                                // Tenta formatar como moeda se parecer valor alto, senão mostra número puro
                                if (val > 0) { 
                                     // Verifica se é valor monetário ou qtd (assumindo monetário para custos)
                                     return `${label}: ${val}`;
                                }
                                return `${label}: ${val}`;
                            }
                        }
                    }
                }
            }
        });
    }

});

// =========================================================
// 5. FUNÇÕES DE MODAL (Globais para funcionar com onclick)
// =========================================================
window.abrirModal = function(modalId) {
    const modal = document.getElementById(modalId);
    const modalContent = modal.querySelector('div');
    
    if (modal) {
        modal.classList.remove('hidden');
        setTimeout(() => {
            modal.classList.remove('opacity-0');
            if (modalContent) {
                modalContent.classList.remove('scale-95');
                modalContent.classList.add('scale-100');
            }
        }, 10);
    }
}

window.fecharModal = function(modalId) {
    const modal = document.getElementById(modalId);
    const modalContent = modal.querySelector('div');
    
    if (modal) {
        modal.classList.add('opacity-0');
        if (modalContent) {
            modalContent.classList.remove('scale-100');
            modalContent.classList.add('scale-95');
        }
        setTimeout(() => {
            modal.classList.add('hidden');
        }, 300);
    }
}

// Fechar ao clicar fora ou ESC
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal-overlay')) {
        fecharModal(e.target.id);
    }
});

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