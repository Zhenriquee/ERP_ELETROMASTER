document.addEventListener('DOMContentLoaded', function() {
    // 1. Inicializar Ícones Lucide
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }

    // 2. Lógica do Menu Mobile (Sidebar Responsiva)
    const btnMenu = document.getElementById('btn-mobile-menu');
    const btnClose = document.getElementById('btn-close-sidebar');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('mobile-overlay');

    function toggleMenu() {
        // Toggle da classe que esconde o sidebar (-translate-x-full)
        // Quando removida, o sidebar aparece (translate-x-0 é o padrão se removermos o negative)
        // Como o sidebar tem '-translate-x-full' por padrão no HTML:
        
        const isClosed = sidebar.classList.contains('-translate-x-full');
        
        if (isClosed) {
            // Abrir
            sidebar.classList.remove('-translate-x-full');
            // Mostrar Overlay
            overlay.classList.remove('hidden');
            setTimeout(() => overlay.classList.remove('opacity-0'), 10); // Fade in
        } else {
            // Fechar
            sidebar.classList.add('-translate-x-full');
            // Esconder Overlay
            overlay.classList.add('opacity-0');
            setTimeout(() => overlay.classList.add('hidden'), 300); // Wait for transition
        }
    }

    if (btnMenu && sidebar && overlay) {
        btnMenu.addEventListener('click', toggleMenu);
        if (btnClose) btnClose.addEventListener('click', toggleMenu);
        overlay.addEventListener('click', toggleMenu); // Fecha ao clicar fora
    }

    // 3. Fechar alertas automaticamente após 5 segundos
    const alertas = document.querySelectorAll('.alert-dismissible');
    alertas.forEach(alerta => {
        setTimeout(() => {
            alerta.style.opacity = '0';
            setTimeout(() => alerta.remove(), 500);
        }, 5000);
    });
});