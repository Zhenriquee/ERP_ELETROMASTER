// src/static/js/operacional.js

document.addEventListener('DOMContentLoaded', function() {
    // 1. Recupera filtro salvo ou usa 'todos' como padrão
    // DICA: Para produção, o padrão ideal pode ser 'todos' ou 'producao'
    const filtroSalvo = localStorage.getItem('filtroProducao') || 'todos';
    filtrarCards(filtroSalvo);

    // 2. Timer de Auto-Refresh (Visual)
    let segundos = 60;
    const timerDisplay = document.getElementById('timerRefresh');
    
    if (timerDisplay) {
        setInterval(() => {
            segundos--;
            timerDisplay.innerText = segundos + 's';
            if (segundos <= 0) {
                window.location.reload();
            }
        }, 1000);
    }
    
    // Inicializa ícones (caso use HTMX ou carregamento dinâmico no futuro)
    if(typeof lucide !== 'undefined') lucide.createIcons();
});

function filtrarCards(status) {
    const cards = document.querySelectorAll('.card-servico');
    const steps = document.querySelectorAll('.step-pipeline');
    const emptyState = document.getElementById('emptyState');
    
    // Salva preferência
    localStorage.setItem('filtroProducao', status);

    // 1. Atualiza Visual dos Botões de Topo (Steps)
    steps.forEach(step => {
        step.classList.remove('ativo', 'ring-2', 'ring-offset-2', 'ring-gray-300', 'ring-blue-500', 'ring-yellow-500');
    });

    // Ativa o botão clicado
    const stepAtivo = document.getElementById(`step-${status}`);
    if(stepAtivo) {
        stepAtivo.classList.add('ativo', 'ring-2', 'ring-offset-2');
        if(status === 'pendente') stepAtivo.classList.add('ring-gray-300');
        if(status === 'producao') stepAtivo.classList.add('ring-blue-500');
        if(status === 'pronto') stepAtivo.classList.add('ring-yellow-500');
    }

    // 2. Filtra os Cards
    let visiveis = 0;
    
    cards.forEach(card => {
        const statusCard = card.dataset.status; // Agora virá limpo do HTML (ex: 'producao')
        
        // Lógica de exibição:
        // Se filtro == 'todos': mostra tudo.
        // Se filtro == statusCard: mostra o que bate.
        const deveMostrar = (status === 'todos') || (statusCard === status);
        
        if (deveMostrar) {
            card.style.display = 'flex';
            card.classList.remove('hidden'); // Garante remoção da classe hidden do Tailwind
            
            // Reinicia animação para dar feedback visual
            card.classList.remove('card-animado');
            void card.offsetWidth; // Trigger reflow (hack para reiniciar CSS animation)
            card.classList.add('card-animado');
            
            visiveis++;
        } else {
            card.style.display = 'none';
        }
    });

    // 3. Estado Vazio (Feedback para o usuário se não houver itens)
    if (emptyState) {
        if (visiveis === 0) {
            emptyState.classList.remove('hidden');
            emptyState.classList.add('flex');
            
            // Atualiza mensagem do Empty State dinamicamente
            const tituloEmpty = emptyState.querySelector('h3');
            if(tituloEmpty) {
                if(status === 'producao') tituloEmpty.innerText = "Nada sendo produzido agora!";
                else if(status === 'pronto') tituloEmpty.innerText = "Nenhum item aguardando entrega!";
                else tituloEmpty.innerText = "Nenhum serviço nesta etapa!";
            }
        } else {
            emptyState.classList.add('hidden');
            emptyState.classList.remove('flex');
        }
    }
}