#!/usr/bin/env python3
"""
MX NEWS - Daily News Aggregator
Fetches motocross news from English sources, translates to Russian, 
and generates static HTML pages.
"""

import os
import re
import json
import hashlib
from datetime import datetime, timedelta
from urllib.request import urlopen, Request
from urllib.error import URLError
from html.parser import HTMLParser
import time
import ssl

# Disable SSL verification for some sites
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

BASE_DIR = '/var/www/mxnews'
NEWS_DATA = os.path.join(BASE_DIR, 'data', 'news.json')

# Sources configuration
SOURCES = {
    'mxgp': {
        'urls': [
            'https://www.mxgp.com/news',
        ],
        'category': 'MXGP',
        'icon': '🏁'
    },
    'supercross': {
        'urls': [
            'https://racerxonline.com/sx',
        ],
        'category': 'Supercross',
        'icon': '🏟️'
    },
    'motogp': {
        'urls': [
            'https://www.motogp.com/en/news',
        ],
        'category': 'MotoGP',
        'icon': '🏍️'
    },
    'fim-rally': {
        'urls': [
            'https://www.fim-moto.com/en/news',
            'https://www.rallyraidnetwork.co.uk/news',
        ],
        'category': 'FIM Rally',
        'icon': '🏜️'
    },
    'gncc': {
        'urls': [
            'https://racerxonline.com/gncc',
        ],
        'category': 'GNCC',
        'icon': '🌲'
    },
    'mxa': {
        'urls': [
            'https://motocrossactionmag.com/',
        ],
        'category': 'Техника',
        'icon': '🔧'
    },
    'crmfr': {
        'urls': [
            'https://motocross.rgpmx.ru/news',
            'https://www.mfr.ru/news',
        ],
        'category': 'ЧР МФР',
        'icon': '🇷🇺'
    },
    'wess': {
        'urls': [
            'https://enduroworldseries.com/news',
        ],
        'category': 'WESS',
        'icon': '🏔️'
    }
}

# Simple translation dictionary (key phrases)
TRANSLATIONS = {
    'supercross': 'суперкросс',
    'motocross': 'мотокросс',
    'championship': 'чемпионат',
    'season': 'сезон',
    'race': 'гонка',
    'rider': 'гонщик',
    'team': 'команда',
    'victory': 'победа',
    'podium': 'подиум',
    'injury': 'травма',
    'returns': 'возвращается',
    'preview': 'предпросмотр',
    'results': 'результаты',
    'standings': 'таблица очков',
    'points': 'очки',
    'broken': 'сломан',
    'knee': 'колено',
    'shoulder': 'плечо',
    'wrist': 'запястье',
    'thumb': 'большой палец',
    'out': 'пропускает',
    'joins': 'присоединился к',
    'signs': 'подписал контракт с',
    'breaks': 'сломал',
    'announces': 'объявил',
    'confirmed': 'подтверждён',
    'schedule': 'расписание',
    'calendar': 'календарь',
    'start': 'старт',
    'finish': 'финиш',
    'lap': 'круг',
    'pole position': 'поул-позиция',
    'hole shot': 'холшот',
    'factory team': 'заводская команда',
    'privateer': 'частник',
    'rookie': 'дебютант',
    'veteran': 'ветеран',
    'fastest': 'быстрейший',
    'crash': 'авария',
    'DNF': 'сход',
    'DNS': 'не стартовал',
    'rally': 'ралли',
    'dakar': 'дакар',
    'moto3': 'мото3',
    'moto2': 'мото2',
    'motogp': 'мотогп',
    'pole': 'поул',
    'grand prix': 'гран-при',
}

def fetch_url(url, max_retries=2):
    """Fetch URL content with retries"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; MXNews/1.0; +https://mxnews.ru/bot)',
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'en-US,en;q=0.5',
    }
    
    for attempt in range(max_retries + 1):
        try:
            req = Request(url, headers=headers)
            with urlopen(req, timeout=15, context=ctx) as response:
                return response.read().decode('utf-8', errors='ignore')
        except Exception as e:
            if attempt < max_retries:
                time.sleep(2)
                continue
            print(f"Failed to fetch {url}: {e}")
            return None

def extract_articles_from_html(html, source_url, category):
    """Extract article links and titles from HTML"""
    articles = []
    
    # Pattern for article links
    patterns = [
        r'<a[^>]*href=["\']([^"\']+)["\'][^>]*>([^<]+)</a>',
        r'<h[23][^>]*>\s*<a[^>]*href=["\']([^"\']+)["\'][^>]*>([^<]+)</a>',
    ]
    
    for pattern in patterns:
        for match in re.finditer(pattern, html, re.IGNORECASE):
            url, title = match.groups()
            title = re.sub(r'<[^>]+>', '', title).strip()
            
            # Filter: only motocross-related, minimum title length
            if len(title) < 20 or len(title) > 200:
                continue
            
            # Skip navigation/footer links
            skip_words = ['cookie', 'privacy', 'terms', 'login', 'sign', 'subscribe', 
                         'contact', 'about', 'advertise', 'shop', 'cart']
            if any(w in title.lower() for w in skip_words):
                continue
            
            # Normalize URL
            if url.startswith('/'):
                from urllib.parse import urljoin
                url = urljoin(source_url, url)
            elif not url.startswith('http'):
                continue
            
            # Check if motocross-related
            mx_keywords = ['motocross', 'supercross', 'mxgp', 'sx', 'rider', 'race', 
                          'kawasaki', 'honda', 'yamaha', 'ktm', 'husqvarna', 'gasgas',
                          'gncc', 'enduro', '250', '450', 'ferrandis', 'webb', 'tomac',
                          'lawrence', 'anderson', 'roczen', 'herlings', 'prado', 'gajser',
                          'laptimes', 'qualifying', 'moto', 'holeshot', 'circuit']
            
            if not any(kw in title.lower() for kw in mx_keywords):
                continue
            
            articles.append({
                'url': url,
                'title': title,
                'category': category,
                'source': source_url,
                'fetched': datetime.now().isoformat()
            })
    
    return articles

def simple_translate(text):
    """Simple word/phrase replacement translation"""
    result = text
    for en, ru in TRANSLATIONS.items():
        # Case-insensitive replacement while preserving some case
        pattern = re.compile(re.escape(en), re.IGNORECASE)
        result = pattern.sub(ru, result)
    return result

def generate_slug(title):
    """Generate URL slug from title"""
    slug = re.sub(r'[^a-zA-Zа-яА-Я0-9\s-]', '', title.lower())
    slug = re.sub(r'\s+', '-', slug.strip())
    return slug[:80]

def load_news_data():
    """Load existing news data"""
    os.makedirs(os.path.dirname(NEWS_DATA), exist_ok=True)
    if os.path.exists(NEWS_DATA):
        with open(NEWS_DATA, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'articles': [], 'last_update': None}

def save_news_data(data):
    """Save news data"""
    with open(NEWS_DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def fetch_all_sources():
    """Fetch news from all sources"""
    all_articles = []
    
    for source_id, config in SOURCES.items():
        print(f"Fetching {config['category']}...")
        
        for url in config['urls']:
            html = fetch_url(url)
            if html:
                articles = extract_articles_from_html(html, url, config['category'])
                all_articles.extend(articles)
                print(f"  Found {len(articles)} articles from {url}")
            time.sleep(1)  # Be polite
    
    return all_articles

def update_news():
    """Main update function"""
    print(f"=== MX NEWS Update: {datetime.now()} ===")
    
    # Load existing data
    data = load_news_data()
    existing_urls = {a['url'] for a in data['articles']}
    
    # Fetch new articles
    new_articles = fetch_all_sources()
    
    # Add only new articles
    added = 0
    for article in new_articles:
        if article['url'] not in existing_urls:
            # Add translated title
            article['title_ru'] = simple_translate(article['title'])
            article['id'] = hashlib.md5(article['url'].encode()).hexdigest()[:10]
            data['articles'].insert(0, article)  # Newest first
            existing_urls.add(article['url'])
            added += 1
    
    # Keep only last 500 articles
    data['articles'] = data['articles'][:500]
    data['last_update'] = datetime.now().isoformat()
    
    save_news_data(data)
    print(f"Added {added} new articles. Total: {len(data['articles'])}")
    
    return added

if __name__ == '__main__':
    update_news()
