/* MX NEWS - Main JavaScript */
document.addEventListener('DOMContentLoaded', function() {
    // === Счётчик посещений (клиентский + серверный) ===
    function initVisitorCounter() {
        const counterKey = 'mxnews_visitor_counter';
        const today = new Date().toDateString();
        
        // Получаем или создаём счётчик в localStorage
        let counterData = JSON.parse(localStorage.getItem(counterKey) || '{}');
        
        // Проверяем, было ли сегодня посещение
        const isNewVisitToday = !counterData.lastVisit || counterData.lastVisit !== today;
        
        if (isNewVisitToday) {
            // Новое посещение сегодня
            counterData.totalVisits = (counterData.totalVisits || 0) + 1;
            counterData.lastVisit = today;
            counterData.lastVisitTime = new Date().toISOString();
            localStorage.setItem(counterKey, JSON.stringify(counterData));
            
            // Отправляем данные на серверный счётчик
            fetch('/stats/counter.php', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    action: 'track_visit',
                    timestamp: new Date().toISOString(),
                    referrer: document.referrer || 'direct'
                })
            })
            .then(response => response.json())
            .then(data => {
                console.log('📊 Статистика посещений:', data);
                
                // Обновляем счётчик в футере с серверными данными
                const footerCounter = document.querySelector('.footer-counter');
                if (footerCounter && data.stats) {
                    footerCounter.textContent = `👁️ ${data.stats.total_visits} посещений (${data.stats.today_visits} сегодня)`;
                    footerCounter.title = `Уникальных посетителей: ${data.stats.unique_visitors}\nСегодня: ${data.stats.today_unique} уникальных`;
                    footerCounter.style.cursor = 'help';
                }
            })
            .catch(error => {
                console.log('⚠️ Не удалось отправить статистику, используем локальные данные');
                updateLocalCounter(counterData);
            });
            
            // Показываем уведомление для новых посетителей
            if (counterData.totalVisits === 1) {
                console.log('🎉 Добро пожаловать на MX NEWS!');
            }
        } else {
            // Уже посещали сегодня, показываем локальные данные
            updateLocalCounter(counterData);
        }
        
        return counterData.totalVisits;
    }
    
    // Функция обновления локального счётчика
    function updateLocalCounter(counterData) {
        const footerCounter = document.querySelector('.footer-counter');
        if (footerCounter) {
            footerCounter.textContent = `👁️ ${counterData.totalVisits} посещений`;
            footerCounter.title = `Последнее посещение: ${new Date(counterData.lastVisitTime).toLocaleString('ru-RU')}`;
            footerCounter.style.cursor = 'help';
        }
    }
    
    // Запускаем счётчик
    const visitCount = initVisitorCounter();
    
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
