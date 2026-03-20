/* MX NEWS - Main JavaScript */
document.addEventListener('DOMContentLoaded', function() {
    // Set current date in header
    const dateEl = document.querySelector('.header-date');
    if (dateEl) {
        const now = new Date();
        const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
        dateEl.textContent = now.toLocaleDateString('ru-RU', options);
    }
    
    // Highlight active nav item and scroll into view
    const currentPath = window.location.pathname;
    document.querySelectorAll('.nav-item a').forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
            // Scroll active item into view
            link.parentElement.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
        }
    });
    
    // Mobile menu toggle
    const menuBtn = document.querySelector('.mobile-menu-btn');
    const navList = document.querySelector('.nav-list');
    if (menuBtn && navList) {
        menuBtn.addEventListener('click', () => {
            navList.classList.toggle('show');
        });
    }
    
    // Lazy load images
    if ('IntersectionObserver' in window) {
        const imgObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    if (img.dataset.src) {
                        img.src = img.dataset.src;
                        img.removeAttribute('data-src');
                    }
                    imgObserver.unobserve(img);
                }
            });
        });
        
        document.querySelectorAll('img[data-src]').forEach(img => {
            imgObserver.observe(img);
        });
    }
});
