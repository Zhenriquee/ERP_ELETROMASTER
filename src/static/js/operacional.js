// src/static/js/operacional.js

document.addEventListener('DOMContentLoaded', function() {
    // Recupera o último filtro usado ou define como 'todos'
    const filtroSalvo = localStorage.getItem('filtroProducao') || 'todos';
    filtrarCards(filtroSalvo);

    // Auto-refresh a cada 60s (mantendo o filtro)
    setTimeout(function(){
        window.location.reload();
    }, 60000);
});

function filtrarCards(status) {
    const cards = document.querySelectorAll('.card-servico');
    const kpis = document.querySelectorAll('.kpi-card');
    
    // 1. Persistir filtro
    localStorage.setItem('filtroProducao', status);

    // 2. Atualizar visual dos KPIs
    kpis.forEach(k => {
        k.classList.remove('kpi-ativo', 'ring-4', 'ring-navy-200');
        k.classList.remove('kpi-inativo');
    });

    if (status !== 'todos') {
        const kpiAtivo = document.getElementById(`kpi-${status}`);
        if(kpiAtivo) {
            kpiAtivo.classList.add('kpi-ativo', 'ring-4', 'ring-navy-200');
            // Deixa os outros inativos
            kpis.forEach(k => {
                if (k !== kpiAtivo) k.classList.add('kpi-inativo');
            });
        }
    }

    // 3. Mostrar/Esconder Cards
    let visiveis = 0;
    cards.forEach(card => {
        if (status === 'todos' || card.dataset.status === status) {
            card.classList.remove('hidden');
            card.classList.add('animate-fade-in'); 
            visiveis++;
        } else {
            card.classList.add('hidden');
            card.classList.remove('animate-fade-in');
        }
    });
}