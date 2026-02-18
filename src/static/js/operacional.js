// src/static/js/operacional.js

document.addEventListener('DOMContentLoaded', function() {
    // 1. Recupera filtro salvo
    const filtroSalvo = localStorage.getItem('filtroProducao') || 'todos';
    filtrarCards(filtroSalvo);

    // 2. Timer de Auto-Refresh
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
    
    // 3. Listener para Validação do Form de Baixa
    const formBaixa = document.getElementById('formBaixa');
    if (formBaixa) {
        formBaixa.addEventListener('submit', function(e) {
            let temErro = false;
            const inputsQtd = document.querySelectorAll('.qtd-consumo');
            const selectsProd = document.querySelectorAll('.produto-consumo');
            
            let algumPreenchido = false;

            inputsQtd.forEach((inp, index) => {
                const sel = selectsProd[index];
                
                if (sel.value) {
                    algumPreenchido = true;
                    const valor = parseFloat(inp.value);
                    if (!valor || valor <= 0) {
                        inp.classList.add('border-red-500');
                        temErro = true;
                    } else {
                        inp.classList.remove('border-red-500');
                    }
                }
            });

            if (temErro) {
                e.preventDefault();
                alert('Atenção: A quantidade consumida deve ser maior que zero.');
            }
        });
    }

    if(typeof lucide !== 'undefined') lucide.createIcons();
});

// --- FUNÇÕES DE FILTRO ---
function filtrarCards(status) {
    const cards = document.querySelectorAll('.card-servico');
    const steps = document.querySelectorAll('.step-pipeline');
    const emptyState = document.getElementById('emptyState');
    
    localStorage.setItem('filtroProducao', status);

    steps.forEach(step => {
        step.classList.remove('ativo', 'ring-2', 'ring-offset-2', 'ring-gray-300', 'ring-blue-500', 'ring-yellow-500');
    });

    const stepAtivo = document.getElementById(`step-${status}`);
    if(stepAtivo) {
        stepAtivo.classList.add('ativo', 'ring-2', 'ring-offset-2');
        if(status === 'pendente') stepAtivo.classList.add('ring-gray-300');
        if(status === 'producao') stepAtivo.classList.add('ring-blue-500');
        if(status === 'pronto') stepAtivo.classList.add('ring-yellow-500');
    }

    let visiveis = 0;
    
    cards.forEach(card => {
        const statusCard = card.dataset.status;
        const deveMostrar = (status === 'todos') || (statusCard === status);
        
        if (deveMostrar) {
            card.style.display = 'flex';
            card.classList.remove('hidden');
            
            card.classList.remove('card-animado');
            void card.offsetWidth; 
            card.classList.add('card-animado');
            
            visiveis++;
        } else {
            card.style.display = 'none';
        }
    });

    if (emptyState) {
        if (visiveis === 0) {
            emptyState.classList.remove('hidden');
            emptyState.classList.add('flex');
            
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
// --- FUNÇÕES DO MODAL DE DETALHES ---
function verDetalhes(descricao, cliente, obs, metragem, tempoLabel, tempoVal) {
    const modal = document.getElementById('modalDetalhesServico');
    if(!modal) return;

    document.getElementById('detDescricao').innerText = descricao || '--';
    document.getElementById('detCliente').innerText = cliente || '--';
    document.getElementById('detObs').innerText = obs || 'Sem observações.';
    
    // Proteção para valores vazios
    document.getElementById('detMetragem').innerText = metragem || 'Não informada';
    document.getElementById('detTempoLabel').innerText = tempoLabel || 'Tempo';
    document.getElementById('detTempo').innerText = tempoVal || '--';
    
    modal.classList.remove('hidden');
    setTimeout(() => {
        modal.classList.remove('opacity-0');
        modal.querySelector('div').classList.remove('scale-95');
    }, 10);
    
    if(typeof lucide !== 'undefined') lucide.createIcons();
}

function fecharModalDetalhes() {
    const modal = document.getElementById('modalDetalhesServico');
    if(!modal) return;
    
    modal.classList.add('opacity-0');
    modal.querySelector('div').classList.add('scale-95');
    
    setTimeout(() => {
        modal.classList.add('hidden');
    }, 300);
}

// --- FUNÇÕES DO MODAL DE BAIXA MANUAL ---
function abrirModalBaixa(itemId) {
    const modal = document.getElementById('modalBaixaMaterial');
    const form = document.getElementById('formBaixa');
    
    if(!modal || !form) return;

    form.action = `/operacional/item/${itemId}/finalizar_com_baixa`;
    
    // Reseta linhas
    const container = document.getElementById('listaConsumo');
    while (container.children.length > 1) {
        container.removeChild(container.lastChild);
    }
    const firstRow = container.querySelector('.linha-consumo');
    if(firstRow) {
        firstRow.querySelector('select').value = "";
        firstRow.querySelector('input').value = "";
        firstRow.querySelector('input').classList.remove('border-red-500');
    }

    modal.classList.remove('hidden');
}

function adicionarLinhaConsumo() {
    const container = document.getElementById('listaConsumo');
    const primeiraLinha = container.querySelector('.linha-consumo');
    
    if (primeiraLinha) {
        const novaLinha = primeiraLinha.cloneNode(true);
        const sel = novaLinha.querySelector('select');
        const inp = novaLinha.querySelector('input');
        sel.value = "";
        inp.value = "";
        inp.classList.remove('border-red-500');
        container.appendChild(novaLinha);
    }
}

function verificarDuplicidadeConsumo(selectAtual) {
    const todosSelects = document.querySelectorAll('.produto-consumo');
    const valorAtual = selectAtual.value;
    
    if (!valorAtual) return;

    let contagem = 0;
    todosSelects.forEach(sel => {
        if (sel.value === valorAtual) contagem++;
    });

    if (contagem > 1) {
        alert('Este produto já foi adicionado na lista de consumo.');
        selectAtual.value = ""; 
    }
}

function fecharModalBaixa() {
    const modal = document.getElementById('modalBaixaMaterial');
    if(modal) modal.classList.add('hidden');
}

// ... (código anterior)

// --- FUNÇÕES GALERIA DE FOTOS ---
function abrirModalFotos(listaFotos) {
    const modal = document.getElementById('modalFotos');
    const container = document.getElementById('galeriaContainer');
    const avisoVazio = document.getElementById('semFotos');
    
    if(!modal) return;

    container.innerHTML = ''; // Limpa anterior

    if (!listaFotos || listaFotos.length === 0) {
        container.classList.add('hidden');
        avisoVazio.classList.remove('hidden');
    } else {
        container.classList.remove('hidden');
        avisoVazio.classList.add('hidden');
        
        listaFotos.forEach(url => {
            const wrapper = document.createElement('div');
            wrapper.className = 'relative group rounded-lg overflow-hidden border border-gray-200 shadow-sm';
            
            const img = document.createElement('img');
            img.src = url;
            img.className = 'w-full h-64 object-cover hover:scale-105 transition-transform duration-300 cursor-pointer';
            img.onclick = () => window.open(url, '_blank'); // Abre original ao clicar
            
            const zoomHint = document.createElement('div');
            zoomHint.className = 'absolute inset-0 bg-black/30 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center pointer-events-none';
            zoomHint.innerHTML = '<span class="text-white text-xs font-bold bg-black/50 px-2 py-1 rounded"><i data-lucide="zoom-in" class="w-4 h-4 inline mr-1"></i> Ampliar</span>';

            wrapper.appendChild(img);
            wrapper.appendChild(zoomHint);
            container.appendChild(wrapper);
        });
    }

    modal.classList.remove('hidden');
    setTimeout(() => {
        modal.classList.remove('opacity-0');
        modal.querySelector('div').classList.remove('scale-95');
    }, 10);
    
    if(typeof lucide !== 'undefined') lucide.createIcons();
}

function fecharModalFotos() {
    const modal = document.getElementById('modalFotos');
    if(!modal) return;
    
    modal.classList.add('opacity-0');
    modal.querySelector('div').classList.add('scale-95');
    setTimeout(() => {
        modal.classList.add('hidden');
    }, 300);
}