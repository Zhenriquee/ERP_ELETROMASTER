// src/static/js/login_controller.js

document.addEventListener('DOMContentLoaded', () => {
    // 1. Inicializa Ícones Lucide
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }

    // 2. Lógica do Slider de Imagens
    const container = document.getElementById('slider-container');
    
    // Se não houver container (ex: mobile), não faz nada
    if (!container) return;

    // LER AS IMAGENS DO ATRIBUTO DATA-IMAGES (Isso resolve sua dúvida #3)
    const imagesData = container.getAttribute('data-images');
    if (!imagesData) return;

    const images = JSON.parse(imagesData);
    let currentIndex = 0;

    // Criar elementos DOM para as imagens
    images.forEach((src, index) => {
        const div = document.createElement('div');
        // Adiciona classes do Tailwind e nossas classes customizadas do CSS novo
        div.className = `bg-slide transition-opacity duration-1000 ease-in-out ${index === 0 ? 'opacity-100' : 'opacity-0'}`;
        div.style.backgroundImage = `url('${src}')`;
        container.appendChild(div);
    });

    const slides = container.querySelectorAll('.bg-slide');

    // Iniciar rotação se houver mais de uma imagem
    if (slides.length > 1) {
        setInterval(() => {
            slides[currentIndex].classList.remove('opacity-100');
            slides[currentIndex].classList.add('opacity-0');

            currentIndex = (currentIndex + 1) % images.length;

            slides[currentIndex].classList.remove('opacity-0');
            slides[currentIndex].classList.add('opacity-100');
        }, 5000); // Troca a cada 5 segundos
    }
});