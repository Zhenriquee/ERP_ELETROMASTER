// src/static/js/orcamento.js

function gerarOrcamentoMultiplo() {
    // 1. Coleta os Dados do Cliente
    const tipo = document.getElementById('tipo_cliente').value;
    let nome = "", doc = "", contato = "", email = "";
    
    if (tipo === 'PF') {
        nome = document.querySelector('input[name="pf_nome"]').value || "Consumidor Final";
        doc = document.querySelector('input[name="pf_cpf"]').value || "";
    } else {
        nome = document.querySelector('input[name="pj_fantasia"]').value || "Empresa";
        doc = document.querySelector('input[name="pj_cnpj"]').value || "";
    }
    contato = document.querySelector('input[name="telefone"]').value || "";
    email = document.querySelector('input[name="email"]').value || "";

    // 2. Coleta os Itens da Tabela
    let linhasHTML = '';
    const linhas = document.querySelectorAll('#listaItens tr');
    
    if(linhas.length === 0) {
        alert("Adicione itens antes de gerar o orçamento!");
        return;
    }

    linhas.forEach(tr => {
        // Pega valores dos inputs dentro da linha
        const desc = tr.querySelector('input[name*="[descricao]"]').value;
        const selProd = tr.querySelector('select[name*="[produto_id]"]');
        
        // Texto do produto (trata caso não tenha seleção)
        const prodNome = selProd.selectedIndex >= 0 ? selProd.options[selProd.selectedIndex].text : '-';
        
        const qtd = tr.querySelector('input[name*="[qtd]"]').value;
        const unit = tr.querySelector('input[name*="[unit]"]').value;
        const total = tr.querySelector('input[name*="[total]"]').value;

        // Monta a linha da tabela para impressão
        linhasHTML += `
            <tr class="border-b border-gray-200">
                <td class="p-3">
                    <span class="font-bold block text-sm">${desc}</span>
                    <span class="text-xs text-gray-500">${prodNome}</span>
                </td>
                <td class="p-3 text-center text-sm">${qtd}</td>
                <td class="p-3 text-right text-sm">R$ ${parseFloat(unit || 0).toFixed(2).replace('.', ',')}</td>
                <td class="p-3 text-right font-bold text-sm">R$ ${parseFloat(total || 0).toFixed(2).replace('.', ',')}</td>
            </tr>
        `;
    });

    // 3. Totais e Observações
    const totalFinal = document.getElementById('displayTotalFinal').innerText;
    const obs = document.querySelector('textarea[name="obs_internas"]').value;

    // 4. Monta o HTML da Janela
    const conteudo = `
        <html>
        <head>
            <title>Orçamento Múltiplo - Eletromaster</title>
            <script src="https://cdn.tailwindcss.com"><\/script>
            <style>
                @media print { 
                    @page { margin: 0; size: A4; } 
                    body { margin: 1.6cm; -webkit-print-color-adjust: exact; } 
                }
            </style>
        </head>
        <body class="bg-white text-gray-800 font-sans p-8">
            <div class="flex justify-between items-start border-b-2 border-gray-800 pb-6 mb-6">
                <div>
                    <h1 class="text-3xl font-bold text-gray-900 uppercase tracking-wide">Eletromaster</h1>
                    <p class="text-gray-500 text-xs uppercase tracking-widest font-bold mt-1">Pintura Eletrostatica</p>
                </div>
                <div class="text-right">
                    <h2 class="text-xl font-bold text-gray-600">ORÇAMENTO</h2>
                    <p class="text-lg font-bold text-red-600">(PRÉVIA)</p>
                    <p class="text-gray-500 text-xs mt-1">Data: ${new Date().toLocaleDateString('pt-BR')}</p>
                </div>
            </div>

            <div class="flex justify-between mb-8">
                <div class="w-1/2 pr-4">
                    <h3 class="text-xs font-bold text-gray-400 uppercase mb-2 border-b">Cliente</h3>
                    <p class="font-bold text-lg">${nome}</p>
                    ${doc ? `<p class="text-sm">CPF/CNPJ: ${doc}</p>` : ''}
                    <p class="text-sm">${contato}</p>
                    <p class="text-sm">${email}</p>
                </div>
                <div class="w-1/2 pl-4 text-right">
                    <h3 class="text-xs font-bold text-gray-400 uppercase mb-2 border-b">Emissor</h3>
                    <p class="font-bold">Eletromaster Ltda.</p>
                </div>
            </div>

            <div class="mb-8">
                <table class="w-full text-left border-collapse">
                    <thead>
                        <tr class="bg-gray-100 text-gray-600 uppercase text-xs">
                            <th class="p-3 border-b-2 border-gray-300">Descrição / Material</th>
                            <th class="p-3 border-b-2 border-gray-300 text-center">Qtd</th>
                            <th class="p-3 border-b-2 border-gray-300 text-right">Unit.</th>
                            <th class="p-3 border-b-2 border-gray-300 text-right">Total</th>
                        </tr>
                    </thead>
                    <tbody>${linhasHTML}</tbody>
                </table>
            </div>

            <div class="flex justify-end mb-8">
                <div class="text-right w-1/3 border-t-2 border-gray-900 pt-2">
                    <span class="text-xs font-bold text-gray-500 uppercase">Valor Total</span>
                    <span class="text-3xl font-black text-navy-900 block mt-1">R$ ${totalFinal}</span>
                </div>
            </div>
            
            ${obs ? `
            <div class="bg-gray-50 p-4 rounded border border-gray-200 text-xs mb-8">
                <h4 class="font-bold text-gray-500 uppercase mb-1">Observações Internas</h4>
                <p>${obs}</p>
            </div>` : ''}

            <div class="text-center text-xs text-gray-400 pt-6 border-t mt-auto">
                <p>Este documento é um orçamento e não garante reserva de estoque sem confirmação.</p>
            </div>

            <script>
                window.onload = function() { window.print(); }
            <\/script>
        </body>
        </html>
    `;

    // 5. Abre a Janela de Impressão
    const janela = window.open('', '_blank', 'width=900,height=600');
    janela.document.write(conteudo);
    janela.document.close();
}