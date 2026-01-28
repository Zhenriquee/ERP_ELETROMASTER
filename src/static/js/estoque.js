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
    
    // Pequeno delay para permitir que o navegador renderize o display:flex antes da opacidade
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
    }, 300); // Tempo igual à transição CSS
}

// Fechar ao clicar no overlay (fundo escuro)
window.onclick = function(event) {
    if (event.target.classList.contains('fixed')) { // Classe genérica do overlay
        fecharModal(event.target.id);
    }
}

// --- FUNÇÕES ESPECÍFICAS DE ESTOQUE ---

// 1. Abrir Modal para NOVO Produto (Limpa os campos)
function abrirModalProduto() {
    const form = document.getElementById('formProduto');
    const titulo = document.getElementById('tituloModalProduto');
    
    // Reseta a rota para a rota padrão de criação (sem ID)
    // OBS: A rota base /estoque/ trata o POST de criação
    form.action = window.location.pathname; 
    
    if(titulo) titulo.innerText = "Novo Produto";
    
    // Limpa campos
    document.getElementById('inputNome').value = "";
    document.getElementById('inputUnidade').value = "CX";
    document.getElementById('inputMinimo').value = "";
    document.getElementById('inputM2').value = "";
    document.getElementById('inputM3').value = "";
    
    abrirModal('modalProduto');
}

// 2. Abrir Modal para EDITAR Produto (Preenche os campos)
function abrirModalEditar(id, nome, unidade, minimo, m2, m3) {
    const form = document.getElementById('formProduto');
    const titulo = document.getElementById('tituloModalProduto');
    
    // Define a rota de edição dinâmica
    form.action = `/estoque/produto/editar/${id}`;
    
    if(titulo) titulo.innerText = "Editar Produto";
    
    // Preenche campos (Trata 'None' ou valores nulos)
    document.getElementById('inputNome').value = nome;
    document.getElementById('inputUnidade').value = unidade;
    
    // Converte 'None' string do Python para vazio
    const trataValor = (val) => (val === 'None' || val === '0.0' || val === '0.00' ? '' : val);
    
    document.getElementById('inputMinimo').value = trataValor(minimo);
    document.getElementById('inputM2').value = trataValor(m2);
    document.getElementById('inputM3').value = trataValor(m3);
    
    abrirModal('modalProduto');
}

// 3. Modal de Movimentação (Estoque)
function abrirModalMovimentacao(id, nome, unidade) {
    const form = document.getElementById('formMovimentacao');
    
    const labelNome = document.getElementById('nomeProdutoMov');
    const labelUnidade = document.getElementById('unidadeProdutoMov');
    
    if(labelNome) labelNome.innerText = nome;
    if(labelUnidade) labelUnidade.innerText = unidade;
    
    // Atualiza a action do form dinamicamente
    // Assume que existe uma rota base e substitui o ID placeholder
    form.action = `/estoque/movimentar/${id}`;
    
    abrirModal('modalMovimentacao');
}

// 4. Abrir Modal de Histórico (Fetch API)
async function abrirModalHistorico(id, nome) {
    const modal = document.getElementById('modalHistorico');
    const titulo = document.getElementById('tituloHistorico');
    const tbody = document.getElementById('corpoTabelaHistorico');
    const loading = document.getElementById('loadingHistorico');
    const vazio = document.getElementById('vazioHistorico');

    // 1. Configurações Iniciais
    titulo.innerText = `Histórico: ${nome}`;
    tbody.innerHTML = ''; // Limpa tabela antiga
    vazio.classList.add('hidden');
    loading.classList.remove('hidden'); // Mostra spinner
    
    abrirModal('modalHistorico'); // Abre o modal vazio com loading

    try {
        // 2. Busca dados no Backend
        const response = await fetch(`/estoque/api/historico/${id}`);
        const dados = await response.json();

        // 3. Renderiza
        loading.classList.add('hidden');

        if (dados.length === 0) {
            vazio.classList.remove('hidden');
        } else {
            dados.forEach(mov => {
                const tr = document.createElement('tr');
                tr.className = "hover:bg-blue-50 transition-colors";

                // Formatação visual baseada no tipo (Entrada = Verde, Saída = Vermelho)
                const isEntrada = mov.tipo === 'entrada';
                const corTexto = isEntrada ? 'text-green-600' : 'text-red-600';
                const sinal = isEntrada ? '+' : '-';
                const icone = isEntrada ? 'arrow-down-circle' : 'arrow-up-circle'; // Down = Entrando na caixa, Up = Saindo

                // Formatação da Origem (Badge)
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
                        <span class="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${badgeOrigem}">
                            ${mov.origem}
                        </span>
                    </td>
                    <td class="px-6 py-3 text-right font-bold ${corTexto}">
                        ${sinal} ${mov.quantidade.toFixed(3).replace('.', ',')}
                    </td>
                    <td class="px-6 py-3 text-right font-bold text-navy-900">
                        ${mov.saldo_novo.toFixed(3).replace('.', ',')}
                    </td>
                    <td class="px-6 py-3 text-xs font-medium">
                        ${mov.usuario}
                    </td>
                    <td class="px-6 py-3 text-xs text-gray-500 italic truncate max-w-xs" title="${mov.observacao}">
                        ${mov.observacao}
                    </td>
                `;
                tbody.appendChild(tr);
            });
            
            // Recarrega ícones Lucide nos novos elementos
            if(typeof lucide !== 'undefined') lucide.createIcons();
        }

    } catch (error) {
        console.error("Erro ao carregar histórico:", error);
        loading.classList.add('hidden');
        tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-red-500 font-bold">Erro ao carregar dados. Tente novamente.</td></tr>`;
    }
}