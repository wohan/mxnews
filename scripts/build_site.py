#!/usr/bin/env python3
"""
MX NEWS - Complete Site Builder
Reads news.json and rebuilds ALL HTML pages with actual article content.
"""

import os
import json
import re
from datetime import datetime
from collections import defaultdict

BASE_DIR = '/var/www/mxnews'
NEWS_DATA = os.path.join(BASE_DIR, 'data', 'news.json')

# All sections config
SECTIONS = {
    'mxgp': {'title': 'MXGP — Чемпионат мира по мотокроссу', 'icon': '🏁', 'categories': ['MXGP', 'MX2']},
    'supercross': {'title': 'AMA Supercross', 'icon': '🏟️', 'categories': ['Supercross', '250SX', '450SX']},
    'crmfr': {'title': 'ЧР МФР — Чемпионат России', 'icon': '🇷🇺', 'categories': ['ЧР МФР']},
    'gncc': {'title': 'GNCC — Кросс-кантри эндуро', 'icon': '🌲', 'categories': ['GNCC']},
    'fim-rally': {'title': 'FIM Rally — Ралли-рейды', 'icon': '🏜️', 'categories': ['FIM Rally', 'Rally']},
    'wess': {'title': 'WESS — World Enduro Super Series', 'icon': '🏔️', 'categories': ['WESS', 'Enduro']},
    'equipment': {'title': 'Техника — Обзоры', 'icon': '🔧', 'categories': ['Техника']},
    'training': {'title': 'Тренировки — Подготовка', 'icon': '💪', 'categories': ['Тренировки']},
}

NAV_ITEMS = [
    ('/', 'Главная'), ('/standings/', 'Таблицы'), ('/calendar/', 'Календарь'),
    ('/mxgp/', 'MXGP'), ('/supercross/', 'Supercross'),
    ('/fim-rally/', 'FIM Rally'), ('/wess/', 'WESS'),
    ('/equipment/', 'Техника'), ('/training/', 'Тренировки'),
]

MONTHS_RU = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
             'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']

def load_news():
    with open(NEWS_DATA, 'r', encoding='utf-8') as f:
        return json.load(f)

def format_date(article):
    """Format date - prefer source date over fetch date"""
    # Try pub_date first (from source), then fetched
    date_str = article.get('pub_date', '') or article.get('fetched', '')
    try:
        if 'T' in date_str:
            dt = datetime.fromisoformat(date_str[:19])
        else:
            dt = datetime.strptime(date_str[:10], '%Y-%m-%d')
        return f"{dt.day} {MONTHS_RU[dt.month-1]} {dt.year}"
    except:
        return date_str[:10] if date_str else ''

def nav_html(active_path=''):
    items = []
    for path, name in NAV_ITEMS:
        active = ' class="active"' if path == active_path else ''
        items.append(f'<li class="nav-item"><a href="{path}"{active}>{name}</a></li>')
    return '\n            '.join(items)

def news_card(article, featured=False):
    title = article.get('title_ru', article.get('title', 'Без заголовка'))
    url = article.get('url', '#')
    category = article.get('category', 'Новости')
    source = article.get('source', '')
    date_str = format_date(article)
    article_id = article.get('id', '')
    
    # Check if article has Russian content
    has_content = bool(article.get('content_ru') or article.get('content_html'))
    
    # Skip articles without translation (return empty string)
    if not has_content:
        return ''
    
    # ALWAYS link to internal article page
    internal_url = f'/article/{article_id}/' if article_id else url
    
    # Extract domain from source for display
    source_domain = ''
    if source:
        m = re.search(r'https?://(?:www\.)?([^/]+)', source)
        if m:
            source_domain = m.group(1)
    
    card_class = 'news-card news-card-featured' if featured else 'news-card'
    
    # Always use internal link (no target _blank for internal pages)
    link_url = internal_url if article_id else url
    
    # Image
    image = article.get('image', '')
    image_html = ''
    if image:
        image_html = f'<img src="{image}" alt="{title[:60]}" class="news-card-image" loading="lazy" onerror="this.style.display=\'none\'">'
    
    return f'''<article class="{card_class}">
            {image_html}
            <div class="news-card-body">
                <span class="news-card-category">{category}</span>
                <h3 class="news-card-title">
                    <a href="{link_url}">{title}</a>
                </h3>
                <div class="news-card-meta">
                    <span class="news-card-date">📅 {date_str}</span>
                    <a href="{url}" target="_blank" rel="noopener" class="news-card-link">🔗 {source_domain or 'Источник'}</a>
                </div>
            </div>
        </article>'''

def generate_main_page(articles_by_cat):
    """Generate main index.html with real articles"""
    
    # Get latest articles across all categories
    all_articles = []
    for cat, arts in articles_by_cat.items():
        all_articles.extend(arts[:5])
    # Sort by publication date (pub_date) first, then by fetch date
    all_articles.sort(key=lambda x: (
        x.get('pub_date', '') or x.get('fetched', '')
    ), reverse=True)
    
    # Featured: first 3
    featured_html = '\n                        '.join([card for card in [news_card(a, featured=(i==0)) for i, a in enumerate(all_articles[:10])] if card])
    
    # MXGP articles
    mxgp_html = '\n                        '.join([card for card in [news_card(a) for a in articles_by_cat.get('MXGP', [])[:10]] if card])
    
    # Supercross articles  
    sx_html = '\n                        '.join([card for card in [news_card(a) for a in articles_by_cat.get('Supercross', [])[:10]] if card])
    
    # MotoGP articles
    motogp_html = '\n                        '.join([card for card in [news_card(a) for a in articles_by_cat.get('MotoGP', [])[:10]] if card])
    
    # Other articles (GNCC, Equipment, Training, etc)
    other_articles = []
    for cat in ['GNCC', 'Техника', 'FIM Rally', 'ЧР МФР']:
        other_articles.extend(articles_by_cat.get(cat, [])[:2])
    other_html = '\n                        '.join([card for card in [news_card(a) for a in other_articles[:12]] if card])
    
    today = datetime.now()
    date_str = f"{today.day} {MONTHS_RU[today.month-1]} {today.year}"
    
    # Count source links
    source_count = 3 + min(4, len(articles_by_cat.get('MXGP', []))) + \
                   min(4, len(articles_by_cat.get('Supercross', []))) + \
                   min(4, len(articles_by_cat.get('MotoGP', []))) + \
                   min(6, len(other_articles))
    
    html = f'''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MX NEWS — Мотокросс новости | MXGP, Supercross, MotoGP, ЧР МФР</title>
    <meta name="description" content="Актуальные новости мотокросса на русском: MXGP, AMA Supercross, MotoGP, ЧР МФР, GNCC, FIM Rally. Таблицы очков, календарь этапов, обзоры техники.">
    <meta name="keywords" content="мотокросс, MXGP, суперкросс, MotoGP, ЧР МФР, мотоспорт, мотогонки, supercross, motocross">
    <meta name="robots" content="index, follow">
    <link rel="canonical" href="https://mxnews.ru/">
    <meta property="og:type" content="website">
    <meta property="og:title" content="MX NEWS — Мотокросс новости">
    <meta property="og:description" content="Актуальные новости мотокросса на русском">
    <meta property="og:locale" content="ru_RU">
    <meta property="og:site_name" content="MX NEWS">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/css/style.css">
    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": "MX NEWS",
        "description": "Новости мотокросса на русском языке",
        "url": "https://mxnews.ru",
        "inLanguage": "ru"
    }}
    </script>
</head>
<body>
    <header class="header">
        <div class="header-top">
            <div>
                <a href="/" class="logo">MX<span>NEWS</span></a>
                <div class="logo-sub">Мотокросс • Суперкросс • Эндуро</div>
            </div>
            <div class="header-date">{date_str}</div>
        </div>
    </header>
    <nav class="nav" aria-label="Основная навигация">
        <ul class="nav-list">
            {nav_html('/')}
        </ul>
    </nav>
    <main class="container">
        <div class="main-grid">
            <div class="news-column">
                <section aria-label="Главные новости">
                    <div class="section-header">
                        <h2 class="section-title">🔥 Главные новости</h2>
                    </div>
                    <div class="news-grid">
                        {featured_html if featured_html else '<div class="empty-state"><p>Загрузка новостей...</p></div>'}
                    </div>
                </section>
                
                <section aria-label="MXGP">
                    <div class="section-header">
                        <h2 class="section-title">🏁 MXGP — Чемпионат мира</h2>
                        <a href="/mxgp/" class="section-more">Все новости →</a>
                    </div>
                    <div class="news-grid">
                        {mxgp_html if mxgp_html else '<div class="empty-state"><p>Загрузка...</p></div>'}
                    </div>
                </section>
                
                <section aria-label="Supercross">
                    <div class="section-header">
                        <h2 class="section-title">🏟️ AMA Supercross</h2>
                        <a href="/supercross/" class="section-more">Все новости →</a>
                    </div>
                    <div class="news-grid">
                        {sx_html if sx_html else '<div class="empty-state"><p>Загрузка...</p></div>'}
                    </div>
                </section>
                
                <section aria-label="MotoGP">
                    <div class="section-header">
                        <h2 class="section-title">🏍️ MotoGP</h2>
                    </div>
                    <div class="news-grid">
                        {motogp_html if motogp_html else '<div class="empty-state"><p>Загрузка...</p></div>'}
                    </div>
                </section>
                
                <section aria-label="Ещё новости">
                    <div class="section-header">
                        <h2 class="section-title">📰 Ещё новости</h2>
                    </div>
                    <div class="news-grid">
                        {other_html if other_html else '<div class="empty-state"><p>Загрузка...</p></div>'}
                    </div>
                </section>
            </div>
            
            <aside class="sidebar">
                <div class="sidebar-widget">
                    <h3 class="widget-title">🏆 MXGP 2026</h3>
                    <p style="font-size:0.85rem;color:var(--text-secondary);">Сезон скоро начнётся. Таблица очков будет обновлена после первого этапа.</p>
                    <a href="/standings/" style="font-size:0.85rem;">Таблицы очков →</a>
                </div>
                
                <div class="sidebar-widget">
                    <h3 class="widget-title">📅 Ближайшие этапы</h3>
                    <ul class="calendar-list">
                        <li class="calendar-item">
                            <div class="calendar-date"><span class="day">22</span>МАР</div>
                            <div class="calendar-info">
                                <div class="calendar-event">Birmingham SX</div>
                                <div class="calendar-location">Бирмингем, США</div>
                            </div>
                        </li>
                        <li class="calendar-item">
                            <div class="calendar-date"><span class="day">5</span>АПР</div>
                            <div class="calendar-info">
                                <div class="calendar-event">MXGP Patagonia</div>
                                <div class="calendar-location">Аргентина</div>
                            </div>
                        </li>
                    </ul>
                    <a href="/calendar/" style="font-size:0.85rem;">Полный календарь →</a>
                </div>
                
                <div class="sidebar-widget">
                    <h3 class="widget-title">📊 Источники</h3>
                    <ul class="footer-links">
                        <li><a href="https://www.mxgp.com" target="_blank" rel="noopener">MXGP.com</a></li>
                        <li><a href="https://racerxonline.com" target="_blank" rel="noopener">Racer X</a></li>
                        <li><a href="https://motocrossactionmag.com" target="_blank" rel="noopener">MXA</a></li>
                        <li><a href="https://www.motogp.com" target="_blank" rel="noopener">MotoGP.com</a></li>
                        <li><a href="https://www.mfr.ru" target="_blank" rel="noopener">МФР</a></li>
                    </ul>
                </div>
            </aside>
        </div>
    </main>
    <footer class="footer">
        <div class="footer-content">
            <div class="footer-about">
                <div class="footer-title">MX NEWS</div>
                <p>Независимый новостной портал о мотокроссе на русском языке. Агрегируем и переводим новости с мировых источников.</p>
            </div>
            <div>
                <div class="footer-title">Чемпионаты</div>
                <ul class="footer-links">
                    <li><a href="/mxgp/">MXGP</a></li>
                    <li><a href="/supercross/">Supercross</a></li>
                    <li><a href="/crmfr/">ЧР МФР</a></li>
                    <li><a href="/gncc/">GNCC</a></li>
                    <li><a href="/fim-rally/">FIM Rally</a></li>
                </ul>
            </div>
            <div>
                <div class="footer-title">Контент</div>
                <ul class="footer-links">
                    <li><a href="/standings/">Таблицы</a></li>
                    <li><a href="/calendar/">Календарь</a></li>
                    <li><a href="/equipment/">Техника</a></li>
                    <li><a href="/training/">Тренировки</a></li>
                    <li><a href="/video/">Видео</a></li>
                </ul>
            </div>
            <div>
                <div class="footer-title">Источники</div>
                <ul class="footer-links">
                    <li><a href="https://www.mxgp.com" target="_blank" rel="noopener">MXGP.com</a></li>
                    <li><a href="https://racerxonline.com" target="_blank" rel="noopener">Racer X</a></li>
                    <li><a href="https://www.mfr.ru" target="_blank" rel="noopener">МФР</a></li>
                </ul>
            </div>
        </div>
        <div class="footer-bottom">
            <p>© 2026 MX NEWS. Все права защищены.</p>
        </div>
    </footer>
    <script src="/js/main.js"></script>
</body>
</html>'''
    
    with open(os.path.join(BASE_DIR, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"✅ index.html — {len(all_articles)} статей")


def generate_section_page(section_id, info, articles):
    """Generate section page with real articles"""
    active_path = f'/{section_id}/'
    
    cards_html = '\n                        '.join([card for card in [news_card(a) for a in articles[:30]] if card])
    if not cards_html:
        cards_html = '<div class="empty-state"><div class="empty-state-icon">' + info['icon'] + '</div><p>Новостей пока нет</p></div>'
    
    html = f'''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{info['title']} — MX NEWS</title>
    <meta name="description" content="{info['title']}: актуальные новости, результаты, таблицы">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/css/style.css">
</head>
<body>
    <header class="header">
        <div class="header-top">
            <div>
                <a href="/" class="logo">MX<span>NEWS</span></a>
                <div class="logo-sub">Мотокросс • Суперкросс • Эндуро</div>
            </div>
            <div class="header-date"></div>
        </div>
    </header>
    <nav class="nav" aria-label="Основная навигация">
        <ul class="nav-list">
            {nav_html(active_path)}
        </ul>
    </nav>
    <main class="container">
        <div class="page-header">
            <nav class="breadcrumb" aria-label="Хлебные крошки">
                <a href="/">Главная</a>
                <span class="breadcrumb-sep">→</span>
                <span>{info['title']}</span>
            </nav>
            <h1>{info['icon']} {info['title']}</h1>
        </div>
        <div class="news-grid">
            {cards_html}
        </div>
    </main>
    <footer class="footer">
        <div class="footer-bottom">
            <p>© 2026 MX NEWS. Все права защищены. <span class="footer-counter" style="margin-left: 20px; font-size: 0.9em; opacity: 0.8;"></span></p>
        </div>
    </footer>
    <script src="/js/main.js"></script>
</body>
</html>'''
    
    path = os.path.join(BASE_DIR, section_id, 'index.html')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"✅ {section_id}/index.html — {len(articles)} статей")


def generate_article_page(article):
    """Generate individual article page"""
    aid = article.get('id', '')
    if not aid:
        return
    
    title = article.get('title_ru', article.get('title', 'Без заголовка'))
    title = title.replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
    category = article.get('category', 'Новости')
    source_url = article.get('url', '')
    date_str = format_date(article)
    
    # Content: prefer Russian, fallback to original, then show link
    content = article.get('content_ru', '')
    if not content:
        content = article.get('content_text', '')
    if not content:
        # Calculate source_domain early for fallback
        tmp_domain = source_url
        m = re.search(r'https?://(?:www\.)?([^/]+)', source_url)
        if m:
            tmp_domain = m.group(1)
        content = f'<div class="article-source" style="margin:2rem 0;padding:1.5rem;"><p>⚠️ Полный текст статьи пока не загружен.</p><p><a href="{source_url}" target="_blank" rel="noopener" style="color:var(--accent);font-weight:700;">→ Читать оригинал на {tmp_domain}</a></p></div>'
    
    # Split into paragraphs if plain text
    if '<p>' not in content:
        paragraphs = [p.strip() for p in content.split('. ') if len(p.strip()) > 10]
        content = '</p>\n<p>'.join(paragraphs)
        content = f'<p>{content}</p>'
    
    # Source domain
    source_domain = source_url
    if source_url:
        m = re.search(r'https?://(?:www\.)?([^/]+)', source_url)
        if m:
            source_domain = m.group(1)
    
    # Section URL for breadcrumb
    section_map = {
        'MXGP': '/mxgp/', 'MX2': '/mxgp/',
        'Supercross': '/supercross/', '250SX': '/supercross/', '450SX': '/supercross/',
        'ЧР МФР': '/crmfr/',
        'GNCC': '/gncc/',
        'MXoN': '/mxon/',
        'FIM Rally': '/fim-rally/', 'Rally': '/fim-rally/',
        'Техника': '/equipment/',
        'Тренировки': '/training/',
        'Видео': '/video/',
    }
    section_url = section_map.get(category, '/mxgp/')
    
    # Images in article
    image = article.get('image', '')
    images = article.get('images', [])
    image_html = f'<meta property="og:image" content="{image}">' if image else ''
    
    # Build gallery of all images
    article_images = ''
    if images:
        for img_url in images[:8]:  # Show up to 8 images
            article_images += f'<img src="{img_url}" alt="{title[:60]}" style="max-width:100%;border-radius:8px;margin-bottom:1rem;" loading="lazy" onerror="this.style.display=\'none\'">\n'
    elif image:
        article_images = f'<img src="{image}" alt="{title[:60]}" style="width:100%;border-radius:8px;margin-bottom:1.5rem;" loading="lazy" onerror="this.style.display=\'none\'">'
    
    html = f'''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} — MX NEWS</title>
    <meta name="description" content="{title[:160]}">
    <meta property="og:type" content="article">
    <meta property="og:title" content="{title}">
    <meta property="og:site_name" content="MX NEWS">
    {image_html}
    <link rel="canonical" href="https://mxnews.ru/article/{aid}/">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/css/style.css">
</head>
<body>
    <header class="header">
        <div class="header-top">
            <div>
                <a href="/" class="logo">MX<span>NEWS</span></a>
                <div class="logo-sub">Мотокросс • Суперкросс • Эндуро</div>
            </div>
            <div class="header-date"></div>
        </div>
    </header>
    <nav class="nav" aria-label="Основная навигация">
        <ul class="nav-list">
            {nav_html()}
        </ul>
    </nav>
    <main class="container">
        <article class="article">
            <div class="article-header">
                <nav class="breadcrumb" aria-label="Хлебные крошки">
                    <a href="/">Главная</a>
                    <span class="breadcrumb-sep">→</span>
                    <a href="{section_url}">{category}</a>
                    <span class="breadcrumb-sep">→</span>
                    <span>Статья</span>
                </nav>
                <span class="article-category">{category}</span>
                <h1 class="article-title">{title}</h1>
                <div class="article-meta">
                    <span>📅 {date_str}</span>
                </div>
            </div>
            <div class="article-content">
                {article_images}
                {content}
            </div>
            <div class="article-source">
                <strong>🔗 Источник:</strong> <a href="{source_url}" target="_blank" rel="noopener">{source_url}</a>
                <br><small>Все права на оригинальный материал принадлежат авторам. Перевод публикуется в информационных целях.</small>
            </div>
        </article>
    </main>
    <footer class="footer">
        <div class="footer-bottom">
            <p>© 2026 MX NEWS. Все права защищены. <span class="footer-counter" style="margin-left: 20px; font-size: 0.9em; opacity: 0.8;"></span></p>
        </div>
    </footer>
    <script src="/js/main.js"></script>
</body>
</html>'''
    
    article_dir = os.path.join(BASE_DIR, 'article', aid)
    os.makedirs(article_dir, exist_ok=True)
    
    with open(os.path.join(article_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(html)


def generate_sitemap():
    """Generate sitemap.xml"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    urls = [
        ('https://mxnews.ru/', '1.0', 'daily'),
        ('https://mxnews.ru/mxgp/', '0.9', 'daily'),
        ('https://mxnews.ru/supercross/', '0.9', 'daily'),
        ('https://mxnews.ru/crmfr/', '0.9', 'daily'),
        ('https://mxnews.ru/gncc/', '0.8', 'daily'),
        ('https://mxnews.ru/mxon/', '0.8', 'weekly'),
        ('https://mxnews.ru/fim-rally/', '0.8', 'daily'),
        ('https://mxnews.ru/standings/', '0.8', 'weekly'),
        ('https://mxnews.ru/calendar/', '0.7', 'weekly'),
        ('https://mxnews.ru/equipment/', '0.7', 'weekly'),
        ('https://mxnews.ru/training/', '0.7', 'weekly'),
        ('https://mxnews.ru/video/', '0.7', 'daily'),
    ]
    
    urls_xml = ''
    for url, priority, freq in urls:
        urls_xml += f'''  <url>
    <loc>{url}</loc>
    <lastmod>{today}</lastmod>
    <changefreq>{freq}</changefreq>
    <priority>{priority}</priority>
  </url>
'''
    
    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{urls_xml}</urlset>'''
    
    with open(os.path.join(BASE_DIR, 'sitemap.xml'), 'w', encoding='utf-8') as f:
        f.write(xml)
    print("✅ sitemap.xml")


def build_all():
    """Main build function"""
    print(f"=== MX NEWS Build: {datetime.now()} ===\n")
    
    data = load_news()
    articles = data.get('articles', [])
    print(f"Загружено {len(articles)} статей из JSON\n")
    
    # Group by category
    articles_by_cat = defaultdict(list)
    for art in articles:
        articles_by_cat[art['category']].append(art)
    
    # Generate main page
    generate_main_page(dict(articles_by_cat))
    
    # Generate section pages
    for section_id, info in SECTIONS.items():
        section_articles = []
        for cat in info['categories']:
            section_articles.extend(articles_by_cat.get(cat, []))
        # Sort by publication date (pub_date) first, then by fetch date
        section_articles.sort(key=lambda x: (
            x.get('pub_date', '') or x.get('fetched', '')
        ), reverse=True)
        generate_section_page(section_id, info, section_articles)
    
    # Generate article pages
    article_count = 0
    for art in articles:
        if art.get('id'):
            generate_article_page(art)
            article_count += 1
    print(f"✅ {article_count} article pages generated")
    
    # Generate sitemap
    generate_sitemap()
    
    print(f"\n✅ Build complete! {len(SECTIONS) + 1} pages generated")


if __name__ == '__main__':
    build_all()
