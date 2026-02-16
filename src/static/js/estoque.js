// src/static/js/estoque.js

document.addEventListener('DOMContentLoaded', function() {
    if(typeof lucide !== 'undefined') lucide.createIcons();
});

// --- FUNÇÕES DE MODAL GENÉRICAS ---

function abrirModal(id) {
    const modal = document.getElementById(id);
    if (!modal) return;
    const content = modal.querySelector('div');
    modal.classList.remove('hidden');
    setTimeout(() => {
        modal.classList.remove('opacity-0');
        if (content) {
            content.classList.remove('scale-95');
            content.classList.add('scale-100');
        }
    }, 10);
}

function fecharModal(id) {
    const modal = document.getElementById(id);
    if (!modal) return;
    const content = modal.querySelector('div');
    modal.classList.add('opacity-0');
    if (content) {
        content.classList.remove('scale-100');
        content.classList.add('scale-95');
    }
    setTimeout(() => {
        modal.classList.add('hidden');
    }, 300);
}

window.onclick = function(event) {
    if (event.target.classList.contains('fixed')) { 
        fecharModal(event.target.id);
    }
}

// --- FUNÇÕES DE ESTOQUE ---

function abrirModalProduto() {
    const form = document.getElementById('formProduto');
    const titulo = document.getElementById('tituloModalProduto');
    
    if(form) {
        form.action = window.location.pathname; 
        form.reset();
    }
    if(titulo) titulo.innerText = "Novo Produto";
    
    // Limpa IDs específicos
    ['inputNome', 'inputUnidade', 'inputAtual', 'inputMinimo', 'inputPrecoM2', 'inputPrecoM3', 'inputConsumoM2', 'inputConsumoM3'].forEach(id => {
        const el = document.getElementById(id);
        if(el) el.value = '';
    });
    
    const elUn = document.getElementById('inputUnidade');
    if(elUn) elUn.value = 'KG';

    abrirModal('modalProduto');
}

function abrirModalEditar(id, nome, unidade, atual, minimo, pm2, pm3, cm2, cm3) {
    const form = document.getElementById('formProduto');
    const titulo = document.getElementById('tituloModalProduto');
    
    if(form) form.action = `/estoque/produto/editar/${id}`;
    if(titulo) titulo.innerText = "Editar Produto";
    
    // TRATA VALORES COM 3 CASAS DECIMAIS
    const trata = (val) => {
        if (!val || val === 'None' || val === '0.0' || val === '0.00' || val === '0.000' || val === '0.0000') return '';
        return val;
    };

    const setVal = (id, val) => {
        const el = document.getElementById(id);
        if(el) el.value = val;
    };

    setVal('inputNome', nome);
    setVal('inputUnidade', unidade);
    setVal('inputAtual', trata(atual));
    setVal('inputMinimo', trata(minimo));
    setVal('inputPrecoM2', trata(pm2));
    setVal('inputPrecoM3', trata(pm3));
    setVal('inputConsumoM2', trata(cm2));
    setVal('inputConsumoM3', trata(cm3));

    abrirModal('modalProduto');
}

// ... Restante do código (Movimentação e Histórico) permanece igual ...
function abrirModalMovimentacao(id, nome, unidade) {
    const form = document.getElementById('formMovimentacao');
    const labelNome = document.getElementById('nomeProdutoMov');
    const labelUnidade = document.getElementById('unidadeProdutoMov');
    if(labelNome) labelNome.innerText = nome;
    if(labelUnidade) labelUnidade.innerText = unidade;
    if(form) form.action = `/estoque/movimentar/${id}`;
    abrirModal('modalMovimentacao');
}

async function abrirModalHistorico(id, nome) {
    const titulo = document.getElementById('tituloHistorico');
    const tbody = document.getElementById('corpoTabelaHistorico');
    const loading = document.getElementById('loadingHistorico');
    const vazio = document.getElementById('vazioHistorico');

    if(titulo) titulo.innerText = `Histórico: ${nome}`;
    if(tbody) tbody.innerHTML = ''; 
    if(vazio) vazio.classList.add('hidden');
    if(loading) loading.classList.remove('hidden');
    
    abrirModal('modalHistorico');

    try {
        const response = await fetch(`/estoque/api/historico/${id}`);
        const dados = await response.json();
        if(loading) loading.classList.add('hidden');

        if (dados.length === 0) {
            if(vazio) vazio.classList.remove('hidden');
        } else {
            dados.forEach(mov => {
                const tr = document.createElement('tr');
                tr.className = "hover:bg-blue-50 transition-colors";
                const isEntrada = mov.tipo === 'entrada';
                const corTexto = isEntrada ? 'text-green-600' : 'text-red-600';
                const sinal = isEntrada ? '+' : '-';
                const icone = isEntrada ? 'arrow-down-circle' : 'arrow-up-circle';
                let badgeOrigem = 'bg-gray-100 text-gray-600';
                if (mov.origem === 'compra') badgeOrigem = 'bg-purple-100 text-purple-700';
                if (mov.origem === 'producao') badgeOrigem = 'bg-orange-100 text-orange-700';
                if (mov.origem === 'manual') badgeOrigem = 'bg-blue-100 text-blue-700';

                tr.innerHTML = `
                    <td class="px-6 py-3 whitespace-nowrap font-mono text-xs">${mov.data}</td>
                    <td class="px-6 py-3">
                        <span class="flex items-center font-bold text-xs ${corTexto} uppercase">
                            <i data-lucide="${icone}" class="w-3 h-3 mr-1"></i> ${mov.tipo}
                        </span>
                    </td>
                    <td class="px-6 py-3">
                        <span class="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${badgeOrigem}">${mov.origem}</span>
                    </td>
                    <td class="px-6 py-3 text-right font-bold ${corTexto}">${sinal} ${mov.quantidade.toFixed(3).replace('.', ',')}</td>
                    <td class="px-6 py-3 text-right font-bold text-navy-900">${mov.saldo_novo.toFixed(3).replace('.', ',')}</td>
                    <td class="px-6 py-3 text-xs font-medium">${mov.usuario}</td>
                    <td class="px-6 py-3 text-xs text-gray-500 italic truncate max-w-xs" title="${mov.observacao}">${mov.observacao}</td>
                `;
                if(tbody) tbody.appendChild(tr);
            });
            if(typeof lucide !== 'undefined') lucide.createIcons();
        }
    } catch (error) {
        console.error("Erro histórico:", error);
        if(loading) loading.classList.add('hidden');
        if(tbody) tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-red-500">Erro ao carregar.</td></tr>`;
    }
}