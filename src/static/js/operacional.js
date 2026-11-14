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

// --- VARIÁVEIS GLOBAIS DE PAGINAÇÃO ---
const ITENS_POR_PAGINA = 10;
let paginaAtual = 1;
let statusAtivoAtual = 'pendente';

// --- FUNÇÕES DE FILTRO E PAGINAÇÃO ---
function filtrarCards(status) {
    statusAtivoAtual = status;
    paginaAtual = 1; // Ao mudar de aba, volta para a página 1
    localStorage.setItem('filtroProducao', status);

    const steps = document.querySelectorAll('.step-pipeline');
    steps.forEach(step => {
        step.classList.remove('ativo', 'ring-2', 'ring-offset-2', 'ring-gray-300', 'ring-blue-500', 'ring-yellow-500', 'ring-orange-500');
    });

    const stepAtivo = document.getElementById(`step-${status}`);
    if(stepAtivo) {
        stepAtivo.classList.add('ativo', 'ring-2', 'ring-offset-2');
        if(status === 'pendente') stepAtivo.classList.add('ring-gray-300');
        if(status === 'producao') stepAtivo.classList.add('ring-blue-500');
        if(status === 'retrabalho') stepAtivo.classList.add('ring-orange-500');
        if(status === 'pronto') stepAtivo.classList.add('ring-yellow-500');
    }

    renderizarPagina();
}

function renderizarPagina() {
    const cards = Array.from(document.querySelectorAll('.card-servico'));
    const emptyState = document.getElementById('emptyState');
    const containerPaginacao = document.getElementById('paginacaoContainer');

    // Filtra os cards que pertencem à aba ativa
    const cardsFiltrados = cards.filter(card => {
        const statusCard = card.dataset.status;
        return (statusAtivoAtual === 'todos') || (statusCard === statusAtivoAtual);
    });

    const totalItens = cardsFiltrados.length;
    const totalPaginas = Math.max(1, Math.ceil(totalItens / ITENS_POR_PAGINA));

    if (paginaAtual > totalPaginas) paginaAtual = totalPaginas;
    if (paginaAtual < 1) paginaAtual = 1;

    const indiceInicio = (paginaAtual - 1) * ITENS_POR_PAGINA;
    const indiceFim = indiceInicio + ITENS_POR_PAGINA;

    // Primeiro oculta todos os cards
    cards.forEach(card => {
        card.style.display = 'none';
        card.classList.add('hidden');
    });

    // Exibe apenas os cards da fatia paginada
    const cardsPagina = cardsFiltrados.slice(indiceInicio, indiceFim);
    cardsPagina.forEach(card => {
        card.style.display = 'flex';
        card.classList.remove('hidden');

        card.classList.remove('card-animado');
        void card.offsetWidth;
        card.classList.add('card-animado');
    });

    // Estado vazio
    if (emptyState) {
        if (totalItens === 0) {
            emptyState.classList.remove('hidden');
            emptyState.classList.add('flex');

            const tituloEmpty = emptyState.querySelector('h3');
            if(tituloEmpty) {
                if(statusAtivoAtual === 'producao') tituloEmpty.innerText = "Nada sendo produzido agora!";
                else if(statusAtivoAtual === 'retrabalho') tituloEmpty.innerText = "Nenhum retrabalho pendente!";
                else if(statusAtivoAtual === 'pronto') tituloEmpty.innerText = "Nenhum item aguardando entrega!";
                else tituloEmpty.innerText = "Nenhum serviço nesta etapa!";
            }
        } else {
            emptyState.classList.add('hidden');
            emptyState.classList.remove('flex');
        }
    }

    // Atualiza controles de paginação
    atualizarControlesPaginacao(totalItens, totalPaginas, indiceInicio, cardsPagina.length);
}

function atualizarControlesPaginacao(totalItens, totalPaginas, indiceInicio, qtdExibida) {
    const container = document.getElementById('paginacaoContainer');
    if (!container) return;

    if (totalItens <= ITENS_POR_PAGINA) {
        // Se houver 10 ou menos itens, esconde a paginação para manter a interface limpa
        container.classList.add('hidden');
        return;
    }
    container.classList.remove('hidden');

    const infoSpan = document.getElementById('paginacaoInfo');
    const totalSpan = document.getElementById('paginacaoTotal');
    if (infoSpan && totalSpan) {
        const de = totalItens === 0 ? 0 : indiceInicio + 1;
        const ate = indiceInicio + qtdExibida;
        infoSpan.innerText = `${de} a ${ate}`;
        totalSpan.innerText = totalItens;
    }

    const btnPrimeira = document.getElementById('btnPagPrimeira');
    const btnAnterior = document.getElementById('btnPagAnterior');
    const btnProxima = document.getElementById('btnPagProxima');
    const btnUltima = document.getElementById('btnPagUltima');

    if (btnPrimeira) btnPrimeira.disabled = (paginaAtual === 1);
    if (btnAnterior) btnAnterior.disabled = (paginaAtual === 1);
    if (btnProxima) btnProxima.disabled = (paginaAtual === totalPaginas);
    if (btnUltima) btnUltima.disabled = (paginaAtual === totalPaginas);

    // Renderiza botões numéricos inteligentes (máximo 5 botões visíveis)
    const botoesContainer = document.getElementById('paginasBotoes');
    if (!botoesContainer) return;
    botoesContainer.innerHTML = '';

    let inicioP = Math.max(1, paginaAtual - 2);
    let fimP = Math.min(totalPaginas, inicioP + 4);
    if (fimP - inicioP < 4) {
        inicioP = Math.max(1, fimP - 4);
    }

    for (let p = inicioP; p <= fimP; p++) {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.innerText = p;
        btn.onclick = () => irParaPagina(p);
        if (p === paginaAtual) {
            btn.className = 'w-8 h-8 rounded-lg text-xs font-bold bg-navy-900 text-white shadow-sm';
        } else {
            btn.className = 'w-8 h-8 rounded-lg text-xs font-bold text-gray-700 hover:bg-gray-100 border border-gray-200 transition-colors';
        }
        botoesContainer.appendChild(btn);
    }

    if (typeof lucide !== 'undefined') lucide.createIcons();
}

function mudarPagina(delta) {
    irParaPagina(paginaAtual + delta);
}

function irParaPagina(p) {
    const cards = Array.from(document.querySelectorAll('.card-servico'));
    const cardsFiltrados = cards.filter(card => {
        const statusCard = card.dataset.status;
        return (statusAtivoAtual === 'todos') || (statusCard === statusAtivoAtual);
    });
    const totalPaginas = Math.max(1, Math.ceil(cardsFiltrados.length / ITENS_POR_PAGINA));

    if (p < 1) p = 1;
    if (p > totalPaginas) p = totalPaginas;

    paginaAtual = p;
    renderizarPagina();

    // Rola suavemente até o topo dos cards para conforto visual
    const grid = document.getElementById('gridCards');
    if (grid) {
        grid.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

function irParaUltimaPagina() {
    const cards = Array.from(document.querySelectorAll('.card-servico'));
    const cardsFiltrados = cards.filter(card => {
        const statusCard = card.dataset.status;
        return (statusAtivoAtual === 'todos') || (statusCard === statusAtivoAtual);
    });
    const totalPaginas = Math.max(1, Math.ceil(cardsFiltrados.length / ITENS_POR_PAGINA));
    irParaPagina(totalPaginas);
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

// --- FUNÇÕES DO MODAL DE RETRABALHO ---
function abrirModalRetrabalho(itemId, quantidadeMaxima, tipoItem) {
    const modal = document.getElementById('modalRetrabalho');
    const form = document.getElementById('formRetrabalho');
    const inputQtd = document.getElementById('qtdRetrabalhoInput');
    const spanMax = document.getElementById('qtdMaxRetrabalho');
    
    if(!modal || !form || !inputQtd) return;

    // Define a rota correta baseada no tipo (para compatibilidade com Venda Multipla vs Venda Simples original, embora agora todos usem item no painel)
    if (tipoItem === 'item') {
        form.action = `/operacional/item/${itemId}/retrabalho`;
    } else {
        form.action = `/operacional/venda/${itemId}/retrabalho`;
    }
    
    inputQtd.max = quantidadeMaxima;
    inputQtd.value = quantidadeMaxima; // Sugere o total por padrão
    spanMax.innerText = quantidadeMaxima;

    modal.classList.remove('hidden');
}

function fecharModalRetrabalho() {
    const modal = document.getElementById('modalRetrabalho');
    if(modal) modal.classList.add('hidden');
}

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