document.addEventListener('DOMContentLoaded', function() {
    if (typeof lucide !== 'undefined') lucide.createIcons();
    window.togglePeriodo();

    const jsonScript = document.getElementById('dados-relatorio');
    if (!jsonScript) return;
    
    const dadosBrutos = JSON.parse(jsonScript.textContent);

    // 2. DEFINIÇÃO DAS COLUNAS
    const defColunas = {
        id: { label: "Venda / Data", align: "left" },
        cliente: { label: "Cliente", align: "left" },
        vendedor: { label: "Vendedor", align: "left" },
        item: { label: "Descrição Item", align: "left", acionaGranular: true },
        produto: { label: "Acabamento", align: "left", acionaGranular: true },
        qtd: { label: "Qtd", align: "center" },
        vunit: { label: "V. Unitário", align: "right", acionaGranular: true },
        vtotal: { label: "V. Total", align: "right" },
        
        // --- NOVA COLUNA CADASTRADA ---
        acresc_desc: { label: "Acrésc/Desc", align: "right" },
        
        vpago: { label: "V. Pago", align: "right" },
        vareceber: { label: "A Receber", align: "right" },
        sprod: { label: "Status Prod.", align: "center" },
        spgto: { label: "Status Pgto", align: "center" }
    };

    const tabelaHead = document.getElementById('tabelaHead');
    const tabelaBody = document.getElementById('tabelaBody');
    const checkboxes = document.querySelectorAll('.chk-col');

    function renderizarTabela() {
        const colunasAtivas = Array.from(checkboxes)
                                  .filter(chk => chk.checked)
                                  .map(chk => chk.value);
        
        const isGranular = colunasAtivas.some(col => defColunas[col].acionaGranular);
        
        let dadosProcessados = [];
        
        if (isGranular) {
            dadosProcessados = dadosBrutos;
        } else {
            let mapaVendas = {};
            dadosBrutos.forEach(row => {
                if (!mapaVendas[row.venda_id]) {
                    mapaVendas[row.venda_id] = { ...row, qtd_somada: 0 };
                }
                mapaVendas[row.venda_id].qtd_somada += row.qtd;
            });
            dadosProcessados = Object.values(mapaVendas);
        }

        let htmlHead = '<tr>';
        colunasAtivas.forEach(col => {
            let classAlign = defColunas[col].align === 'right' ? 'text-right' : (defColunas[col].align === 'center' ? 'text-center' : 'text-left');
            htmlHead += `<th class="px-4 py-3 ${classAlign}">${defColunas[col].label}</th>`;
        });
        htmlHead += '</tr>';
        tabelaHead.innerHTML = htmlHead;

        let htmlBody = '';
        if (dadosProcessados.length === 0) {
            htmlBody = `<tr><td colspan="${colunasAtivas.length}" class="text-center py-8 text-gray-400">Nenhum dado encontrado.</td></tr>`;
        } else {
            dadosProcessados.forEach(row => {
                htmlBody += `<tr class="hover:bg-gray-50 transition-colors">`;
                
                colunasAtivas.forEach(col => {
                    let td = '';
                    let align = defColunas[col].align === 'right' ? 'text-right' : (defColunas[col].align === 'center' ? 'text-center' : 'text-left');
                    
                    switch(col) {
                        case 'id': 
                            td = `<span class="font-bold text-navy-900">#${row.venda_id}</span><br><span class="text-[10px] text-gray-500">${row.data_fmt}</span>`; break;
                        case 'cliente': 
                            td = `<span class="font-bold truncate max-w-[150px] block">${row.cliente}</span>`; break;
                        case 'vendedor': 
                            td = `<span class="text-xs text-gray-600">${row.vendedor}</span>`; break;
                        case 'item': 
                            td = `<span class="font-medium text-xs">${row.item_desc}</span>`; break;
                        case 'produto': 
                            td = `<span class="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded">${row.produto}</span>`; break;
                        case 'qtd': 
                            let valorQtd = isGranular ? row.qtd : row.qtd_somada;
                            td = `<span class="font-bold text-gray-700">${valorQtd}</span>`; break;
                        case 'vunit': 
                            td = `<span class="text-xs text-gray-500">R$ ${row.valor_unit.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</span>`; break;
                        case 'vtotal': 
                            let vtot = isGranular ? row.valor_total_item : row.valor_total_venda;
                            td = `<span class="font-bold text-navy-900 whitespace-nowrap">R$ ${vtot.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</span>`; break;
                        
                        // --- NOVA LÓGICA DE CÁLCULO DE ACRÉSCIMO/DESCONTO ---
                        case 'acresc_desc':
                            let saldoVenda = row.valor_acrescimo_venda - row.valor_desconto_venda;
                            // Se estiver granular, divide o saldo entre os itens da venda. Se agrupado, mostra o total.
                            let valorExibir = isGranular ? (saldoVenda / (row.qtd_itens_venda || 1)) : saldoVenda;
                            
                            let corClass = valorExibir > 0 ? 'text-green-600' : (valorExibir < 0 ? 'text-red-600' : 'text-gray-500');
                            let pref = valorExibir > 0 ? '+' : '';
                            td = `<span class="font-bold ${corClass} whitespace-nowrap">${pref} R$ ${valorExibir.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</span>`; 
                            break;

                        case 'vpago': 
                            td = `<span class="font-bold text-green-600 whitespace-nowrap">R$ ${row.valor_pago_venda.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</span>`; break;
                        case 'vareceber': 
                            td = `<span class="font-bold text-orange-600 whitespace-nowrap">R$ ${row.a_receber_venda.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</span>`; break;
                        case 'sprod': 
                            let statusProd = isGranular ? row.status_prod_item : row.status_prod_venda;
                            td = getBadgeProducao(statusProd);
                            break;
                        case 'spgto': 
                            td = getBadgePagamento(row.status_pgto, row.a_receber_venda);
                            break;
                    }
                    htmlBody += `<td class="px-4 py-3 ${align}">${td}</td>`;
                });
                
                htmlBody += `</tr>`;
            });
        }
        tabelaBody.innerHTML = htmlBody;
        if (typeof lucide !== 'undefined') lucide.createIcons();
    }

    function getBadgeProducao(status) {
        if(status === 'pendente') return `<span class="px-2 py-1 bg-gray-100 text-gray-600 rounded text-[10px] font-bold uppercase">Fila</span>`;
        if(status === 'producao') return `<span class="px-2 py-1 bg-blue-100 text-blue-700 rounded text-[10px] font-bold uppercase">Produção</span>`;
        if(status === 'retrabalho') return `<span class="px-2 py-1 bg-orange-100 text-orange-700 rounded text-[10px] font-bold uppercase">Retrabalho</span>`;
        if(status === 'pronto') return `<span class="px-2 py-1 bg-yellow-100 text-yellow-700 rounded text-[10px] font-bold uppercase">Pronto</span>`;
        if(status === 'entregue') return `<span class="px-2 py-1 bg-green-100 text-green-700 rounded text-[10px] font-bold uppercase">Entregue</span>`;
        if(status === 'cancelado') return `<span class="px-2 py-1 bg-red-100 text-red-700 rounded text-[10px] font-bold uppercase">Cancelado</span>`;
        return status;
    }

    function getBadgePagamento(status, falta) {
        if(status === 'pago') return `<span class="text-green-600 font-bold text-[10px] uppercase"><i data-lucide="check-circle" class="w-3 h-3 inline"></i> Pago</span>`;
        if(status === 'parcial') return `<span class="text-orange-500 font-bold text-[10px] uppercase">Parcial</span><br><span class="text-[9px] text-gray-400">R$ ${falta.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</span>`;
        return `<span class="text-red-500 font-bold text-[10px] uppercase">Pendente</span>`;
    }

    checkboxes.forEach(chk => {
        chk.addEventListener('change', renderizarTabela);
    });

    renderizarTabela();
});

window.togglePeriodo = function() {
    const radio = document.querySelector('input[name="tipo_periodo"]:checked');
    if(!radio) return;
    const tipo = radio.value;
    const divMesAno = document.getElementById('filtroMesAno');
    const divDatas = document.getElementById('filtroDatas');
    
    if (tipo === 'mes') {
        if(divMesAno) divMesAno.classList.remove('hidden');
        if(divDatas) divDatas.classList.add('hidden');
    } else {
        if(divMesAno) divMesAno.classList.add('hidden');
        if(divDatas) divDatas.classList.remove('hidden');
    }
};