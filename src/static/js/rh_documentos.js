// src/static/js/rh_documentos.js

// --- FUNÇÃO PARA ATUALIZAR FEEDBACK DE UPLOAD ---
// Precisa ser global para ser chamada pelo onchange no HTML
window.atualizarFeedbackArquivo = function(input) {
    const area = document.getElementById('area-upload');
    const icone = document.getElementById('icone-upload');
    const texto = document.getElementById('texto-upload');
    const nomeArquivo = document.getElementById('nome-arquivo');

    if (input.files && input.files[0]) {
        const arquivo = input.files[0];
        
        // 1. Muda a cor da borda e fundo
        area.classList.remove('border-gray-300', 'hover:bg-gray-50');
        area.classList.add('border-green-400', 'bg-green-50');
        
        // 2. Muda o ícone para check
        icone.classList.remove('text-gray-400');
        icone.classList.add('text-green-600');
        icone.setAttribute('data-lucide', 'check-circle'); 
        
        // 3. Esconde texto padrão e mostra nome do arquivo
        texto.classList.add('hidden');
        nomeArquivo.textContent = arquivo.name;
        nomeArquivo.classList.remove('hidden');
        
        // Atualiza os ícones na tela (para o novo check-circle aparecer)
        if(typeof lucide !== 'undefined') lucide.createIcons();
    } else {
        // Se cancelar, reseta
        area.classList.add('border-gray-300', 'hover:bg-gray-50');
        area.classList.remove('border-green-400', 'bg-green-50');
        
        icone.classList.add('text-gray-400');
        icone.classList.remove('text-green-600');
        icone.setAttribute('data-lucide', 'file-up');

        texto.classList.remove('hidden');
        nomeArquivo.classList.add('hidden');
        
        if(typeof lucide !== 'undefined') lucide.createIcons();
    }
}

// --- FUNÇÕES DO MODAL DE PREVIEW ---
window.abrirPreview = function(url, tipo, titulo) {
    const modal = document.getElementById('previewModal');
    const modalContainer = document.getElementById('previewContainer');
    const previewImage = document.getElementById('previewImage');
    const previewFrame = document.getElementById('previewFrame');
    const previewTitle = document.getElementById('previewTitle');
    const previewLoading = document.getElementById('previewLoading');

    if(!modal) return;

    // Reseta estados
    previewImage.classList.add('hidden');
    previewFrame.classList.add('hidden');
    previewLoading.classList.remove('hidden');
    previewImage.src = '';
    previewFrame.src = '';
    previewTitle.textContent = titulo;

    // Exibe Modal
    modal.classList.remove('hidden');
    // Pequeno delay para animação CSS funcionar
    setTimeout(() => {
        modal.classList.remove('opacity-0');
        modalContainer.classList.remove('scale-95');
    }, 10);

    // Carrega conteúdo baseado no tipo
    if (['jpg', 'jpeg', 'png'].includes(tipo)) {
        previewImage.src = url;
        previewImage.onload = () => {
            previewLoading.classList.add('hidden');
            previewImage.classList.remove('hidden');
        };
    } else if (tipo === 'pdf') {
        previewFrame.src = url;
        // PDFs podem demorar um pouco para renderizar no iframe
        setTimeout(() => {
             previewLoading.classList.add('hidden');
             previewFrame.classList.remove('hidden');
        }, 500);
         previewFrame.onload = () => {
             previewLoading.classList.add('hidden');
             previewFrame.classList.remove('hidden');
         };
    }
    
    if(typeof lucide !== 'undefined') lucide.createIcons();
}

window.fecharPreview = function() {
    const modal = document.getElementById('previewModal');
    const modalContainer = document.getElementById('previewContainer');
    const previewImage = document.getElementById('previewImage');
    const previewFrame = document.getElementById('previewFrame');

    if(!modal) return;

    modal.classList.add('opacity-0');
    modalContainer.classList.add('scale-95');
    
    setTimeout(() => {
        modal.classList.add('hidden');
        previewImage.src = '';
        previewFrame.src = '';
    }, 300);
}

// --- EVENT LISTENERS (Ao carregar a página) ---
document.addEventListener('DOMContentLoaded', function() {
    // Inicializa ícones
    if(typeof lucide !== 'undefined') lucide.createIcons();

    const modal = document.getElementById('previewModal');

    // Fechar ao clicar no fundo escuro
    if (modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === modal) fecharPreview();    
        });
    }

    // Fechar com a tecla ESC
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            if (modal && !modal.classList.contains('hidden')) {
                fecharPreview();
            }
        }
    });
});