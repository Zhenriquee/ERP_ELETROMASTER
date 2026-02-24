// src/static/js/orcamento.js

function gerarOrcamentoSimples(vendedorNome, logoUrl) {
    // 1. Coleta os Dados do Formulário
    const isPF = document.querySelector('input[name="tipo_cliente"][value="PF"]').checked;
    
    let cliente = {};
    if (isPF) {
        cliente.nome = document.querySelector('input[name="pf_nome"]').value || "Cliente não informado";
        cliente.doc = document.querySelector('input[name="pf_cpf"]').value || "";
    } else {
        cliente.nome = document.querySelector('input[name="pj_fantasia"]').value || "Empresa não informada";
        cliente.doc = document.querySelector('input[name="pj_cnpj"]').value || "";
    }
    cliente.telefone = document.querySelector('input[name="telefone"]').value || "";
    cliente.email = document.querySelector('input[name="email"]').value || "";

    // Dados do Serviço
    const descServico = document.querySelector('textarea[name="descricao_servico"]').value || "-";
    const selectProd = document.getElementById('select-produto');
    const produtoNome = selectProd.options[selectProd.selectedIndex].text;
    
    const dim1 = document.getElementById('dimensao_1').value;
    const dim2 = document.getElementById('dimensao_2').value;
    const qtd = document.getElementById('quantidade_pecas').value;
    
    // Financeiro
    const total = document.getElementById('resumo-total').innerText;
    const obs = document.querySelector('textarea[name="observacoes_internas"]').value;

    // Data formatada
    const dataHoje = new Date().toLocaleDateString('pt-BR');

    // 2. Monta o HTML da Janela de Impressão
    const conteudo = `
        <html>
        <head>
            <title>Orçamento - Eletromaster</title>
            <script src="https://cdn.tailwindcss.com"></script>
            <style>
                @media print { 
                    @page { margin: 0; size: A4; } 
                    body { margin: 1.6cm; -webkit-print-color-adjust: exact; } 
                }
            </style>
        </head>
        <body class="bg-white text-gray-800 font-sans p-8">
            <div class="flex justify-between items-start border-b-2 border-gray-800 pb-6 mb-6">
                <div class="flex items-center gap-4">
                    <img src="${logoUrl}" class="h-32 w-auto object-contain">
                    <div>
                        <h1 class="text-3xl font-bold text-gray-900 uppercase">Eletromaster</h1>
                        <p class="text-sm font-bold text-gray-600">CNPJ: 63.172.616/0001-60</p>
                        <p class="text-gray-500 text-xs uppercase tracking-widest font-bold mt-1">Pintura Eletrostática & Serviços</p>
                    </div>
                </div>
                <div class="text-right">
                    <h2 class="text-xl font-bold text-gray-600">ORÇAMENTO</h2>
                    <p class="text-lg font-bold text-red-600">(PRÉVIA)</p>
                    <p class="text-gray-500 text-xs mt-1">Data: ${dataHoje}</p>
                </div>
            </div>

            <div class="flex justify-between mb-8">
                <div class="w-1/2">
                    <h3 class="text-xs font-bold text-gray-400 uppercase mb-2 border-b">Cliente</h3>
                    <p class="font-bold text-lg">${cliente.nome}</p>
                    <p>${cliente.doc}</p>
                    <p>${cliente.telefone}</p>
                    <p>${cliente.email}</p>
                </div>
                <div class="w-1/2 text-right">
                    <h3 class="text-xs font-bold text-gray-400 uppercase mb-2 border-b">Emissor</h3>
                    <p class="font-bold">Eletromaster Ltda.</p>
                    <p>Vendedor: ${vendedorNome}</p>
                </div>
            </div>

            <table class="w-full text-left border-collapse mb-8">
                <thead>
                    <tr class="bg-gray-100 text-gray-600 uppercase text-xs">
                        <th class="p-3 border-b-2 border-gray-300">Descrição</th>
                        <th class="p-3 border-b-2 border-gray-300 text-center">Qtd</th>
                        <th class="p-3 border-b-2 border-gray-300 text-right">Total</th>
                    </tr>
                </thead>
                <tbody>
                    <tr class="border-b border-gray-200">
                        <td class="p-3">
                            <span class="font-bold block">${descServico}</span>
                            <span class="text-xs text-gray-500">${produtoNome} (${dim1} x ${dim2})</span>
                        </td>
                        <td class="p-3 text-center">${qtd}</td>
                        <td class="p-3 text-right font-bold">R$ ${total}</td>
                    </tr>
                </tbody>
            </table>

            <div class="flex justify-end mb-12">
                <div class="text-right">
                    <span class="text-xl font-black text-gray-900 border-t-2 border-gray-900 pt-2 block">
                        TOTAL: R$ ${total}
                    </span>
                </div>
            </div>

            ${obs ? `<div class="bg-gray-50 p-4 rounded border text-xs"><h4 class="font-bold">Observações</h4><p>${obs}</p></div>` : ''}
            
            <script>
                window.onload = function() { window.print(); }
            </script>
        </body>
        </html>
    `;

    // 3. Abre a Janela
    const janela = window.open('', '_blank', 'width=900,height=600');
    janela.document.write(conteudo);
    janela.document.close();
}


// =========================================================================
// NOVA FUNÇÃO: GERAR ORÇAMENTO PARA MÚLTIPLOS ITENS
// =========================================================================
function gerarOrcamentoMultiplo(vendedorNome, logoUrl) {
    // 1. Coleta os Dados do Formulário do Cliente
    const isPF = document.querySelector('input[name="tipo_cliente"][value="PF"]').checked;
    
    let cliente = {};
    if (isPF) {
        cliente.nome = document.querySelector('input[name="pf_nome"]').value || "Cliente não informado";
        cliente.doc = document.querySelector('input[name="pf_cpf"]').value || "";
    } else {
        cliente.nome = document.querySelector('input[name="pj_fantasia"]').value || "Empresa não informada";
        cliente.doc = document.querySelector('input[name="pj_cnpj"]').value || "";
    }
    cliente.telefone = document.querySelector('input[name="telefone"]').value || "";
    cliente.email = document.querySelector('input[name="email"]').value || "";

    // 2. Coleta os Itens da Tabela
    const linhas = document.querySelectorAll('#listaItens tr');
    if (linhas.length === 0) {
        alert("Adicione pelo menos um item para gerar o orçamento.");
        return;
    }

    let itensHTML = '';
    linhas.forEach(linha => {
        const desc = linha.querySelector('input[name$="[descricao]"]')?.value || '-';
        const selectProd = linha.querySelector('select[name$="[produto_id]"]');
        const prod = selectProd && selectProd.selectedIndex >= 0 ? selectProd.options[selectProd.selectedIndex].text : '-';
        const qtd = linha.querySelector('input[name$="[qtd]"]')?.value || '1';
        const unit = linha.querySelector('input[name$="[unit]"]')?.value || '0.00';
        const totalLinha = linha.querySelector('input[name$="[total]"]')?.value || '0.00';

        itensHTML += `
            <tr class="border-b border-gray-200">
                <td class="p-3">
                    <span class="font-bold block">${desc}</span>
                    <span class="text-xs text-gray-500">${prod}</span>
                </td>
                <td class="p-3 text-center">${qtd}</td>
                <td class="p-3 text-right">R$ ${parseFloat(unit).toFixed(2).replace('.', ',')}</td>
                <td class="p-3 text-right font-bold">R$ ${parseFloat(totalLinha).toFixed(2).replace('.', ',')}</td>
            </tr>
        `;
    });
    
    // 3. Financeiro
    // O span displayTotal tem o texto "R$ 0,00". Removemos a string e deixamos apenas o número.
    const totalHtml = document.getElementById('displayTotal').innerText.replace('R$ ', '');
    const obs = document.querySelector('textarea[name="obs_internas"]')?.value || "";

    // Data formatada
    const dataHoje = new Date().toLocaleDateString('pt-BR');

    // 4. Monta o HTML da Janela de Impressão
    const conteudo = `
        <html>
        <head>
            <title>Orçamento - Eletromaster</title>
            <script src="https://cdn.tailwindcss.com"></script>
            <style>
                @media print { 
                    @page { margin: 0; size: A4; } 
                    body { margin: 1.6cm; -webkit-print-color-adjust: exact; } 
                }
            </style>
        </head>
        <body class="bg-white text-gray-800 font-sans p-8">
            <div class="flex justify-between items-start border-b-2 border-gray-800 pb-6 mb-6">
                <div class="flex items-center gap-4">
                    <img src="${logoUrl}" class="h-32 w-auto object-contain">
                    <div>
                        <h1 class="text-3xl font-bold text-gray-900 uppercase">Eletromaster</h1>
                        <p class="text-sm font-bold text-gray-600">CNPJ: 63.172.616/0001-60</p>
                        <p class="text-gray-500 text-xs uppercase tracking-widest font-bold mt-1">Pintura Eletrostática & Serviços</p>
                    </div>
                </div>
                <div class="text-right">
                    <h2 class="text-xl font-bold text-gray-600">ORÇAMENTO</h2>
                    <p class="text-lg font-bold text-red-600">(PRÉVIA MÚLTIPLA)</p>
                    <p class="text-gray-500 text-xs mt-1">Data: ${dataHoje}</p>
                </div>
            </div>

            <div class="flex justify-between mb-8">
                <div class="w-1/2">
                    <h3 class="text-xs font-bold text-gray-400 uppercase mb-2 border-b">Cliente</h3>
                    <p class="font-bold text-lg">${cliente.nome}</p>
                    <p>${cliente.doc}</p>
                    <p>${cliente.telefone}</p>
                    <p>${cliente.email}</p>
                </div>
                <div class="w-1/2 text-right">
                    <h3 class="text-xs font-bold text-gray-400 uppercase mb-2 border-b">Emissor</h3>
                    <p class="font-bold">Eletromaster Ltda.</p>
                    <p>Vendedor: ${vendedorNome}</p>
                </div>
            </div>

            <table class="w-full text-left border-collapse mb-8">
                <thead>
                    <tr class="bg-gray-100 text-gray-600 uppercase text-xs">
                        <th class="p-3 border-b-2 border-gray-300">Item / Acabamento</th>
                        <th class="p-3 border-b-2 border-gray-300 text-center">Qtd</th>
                        <th class="p-3 border-b-2 border-gray-300 text-right">Unitário</th>
                        <th class="p-3 border-b-2 border-gray-300 text-right">Total</th>
                    </tr>
                </thead>
                <tbody>
                    ${itensHTML}
                </tbody>
            </table>

            <div class="flex justify-end mb-12">
                <div class="text-right">
                    <span class="text-xl font-black text-gray-900 border-t-2 border-gray-900 pt-2 block">
                        TOTAL: R$ ${totalHtml}
                    </span>
                </div>
            </div>

            ${obs ? `<div class="bg-gray-50 p-4 rounded border text-xs"><h4 class="font-bold">Observações</h4><p>${obs}</p></div>` : ''}
            
            <script>
                window.onload = function() { window.print(); }
            </script>
        </body>
        </html>
    `;

    // Abre a Janela
    const janela = window.open('', '_blank', 'width=900,height=600');
    janela.document.write(conteudo);
    janela.document.close();
}