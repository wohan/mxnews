#!/usr/bin/env python3
"""
MX NEWS - Fast Article Fetcher + Google Translate
Uses deep-translator (Google Translate) for fast translation.
"""

import os
import re
import json
import time
from datetime import datetime
from urllib.request import urlopen, Request
import ssl

from deep_translator import GoogleTranslator

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

BASE_DIR = '/var/www/mxnews'
NEWS_DATA = os.path.join(BASE_DIR, 'data', 'news.json')
ARTICLES_DIR = os.path.join(BASE_DIR, 'data', 'articles')

os.makedirs(ARTICLES_DIR, exist_ok=True)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; MXNews/1.0)',
    'Accept': 'text/html,application/xhtml+xml',
    'Accept-Language': 'en-US,en;q=0.5',
}

# Initialize translator
translator = GoogleTranslator(source='en', target='ru')

MAX_CHUNK = 4800  # Google Translate limit

def fetch_url(url, timeout=15):
    try:
        req = Request(url, headers=HEADERS)
        with urlopen(req, timeout=timeout, context=ctx) as response:
            return response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"  ❌ {url[:60]}...: {e}")
        return None

def translate_text(text):
    """Fast translation via Google Translate"""
    if not text or len(text) < 5:
        return text
    
    # Split into chunks if needed
    chunks = []
    while len(text) > MAX_CHUNK:
        idx = text[:MAX_CHUNK].rfind('. ')
        if idx < MAX_CHUNK // 2:
            idx = MAX_CHUNK
        chunks.append(text[:idx])
        text = text[idx:].strip()
    if text:
        chunks.append(text)
    
    translated_parts = []
    for chunk in chunks:
        if len(chunk) < 5:
            translated_parts.append(chunk)
            continue
        try:
            result = translator.translate(chunk)
            translated_parts.append(result if result else chunk)
        except Exception as e:
            print(f"  ⚠️ Translate error: {e}")
            translated_parts.append(chunk)
        time.sleep(0.1)  # Small delay to avoid rate limits
    
    return ' '.join(translated_parts)

def extract_article_content(html):
    """Extract main article content, images, and publish date from HTML"""
    if not html:
        return None, None, None, None
    
    title = None
    title_match = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.DOTALL | re.IGNORECASE)
    if title_match:
        title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip()
    
    # Extract publish date from source
    pub_date = None
    date_match = re.search(r'<meta[^>]*property="article:published_time"[^>]*content="([^"]+)"', html, re.IGNORECASE)
    if date_match:
        pub_date = date_match.group(1)[:10]
    if not pub_date:
        date_match = re.search(r'"datePublished"\s*:\s*"([^"]+)"', html, re.IGNORECASE)
        if date_match:
            pub_date = date_match.group(1)[:10]
    if not pub_date:
        time_match = re.search(r'<time[^>]*datetime="([^"]+)"', html, re.IGNORECASE)
        if time_match:
            pub_date = time_match.group(1)[:10]
    
    # Extract ALL images from article
    images = []
    
    # Try og:image first
    og_match = re.search(r'<meta[^>]*property="og:image"[^>]*content="([^"]+)"', html, re.IGNORECASE)
    if og_match and 'logo' not in og_match.group(1).lower():
        images.append(og_match.group(1))
    
    # Try twitter:image
    tw_match = re.search(r'<meta[^>]*name="twitter:image"[^>]*content="([^"]+)"', html, re.IGNORECASE)
    if tw_match and tw_match.group(1) not in images and 'logo' not in tw_match.group(1).lower():
        images.append(tw_match.group(1))
    
    # Find ALL images in article content
    content_match = re.search(r'<article[^>]*>(.*?)</article>', html, re.DOTALL | re.IGNORECASE)
    if content_match:
        for img_match in re.finditer(r'<img[^>]*src="(https?://[^"]+\.(?:jpg|jpeg|png|webp)[^"]*)"', content_match.group(1), re.IGNORECASE):
            url = img_match.group(1)
            if url not in images and 'logo' not in url.lower() and 'avatar' not in url.lower() and 'icon' not in url.lower():
                images.append(url)
    
    # Fallback: find images in full HTML
    if not images:
        for img_match in re.finditer(r'<img[^>]*src="(https?://[^"]+\.(?:jpg|jpeg|png|webp)[^"]*)"', html, re.IGNORECASE):
            url = img_match.group(1)
            if url not in images and 'logo' not in url.lower() and 'avatar' not in url.lower() and 'icon' not in url.lower():
                images.append(url)
                if len(images) >= 5:
                    break
    
    featured_image = images[0] if images else None
    
    content = ''
    
    # Try article tag
    article_match = re.search(r'<article[^>]*>(.*?)</article>', html, re.DOTALL | re.IGNORECASE)
    if article_match:
        content = article_match.group(1)
    
    # Try content divs
    if not content:
        for pattern in [
            r'<div[^>]*class="[^"]*(?:entry-content|post-content|article-content|article__body)[^"]*"[^>]*>(.*?)</div>\s*</div>',
            r'<div[^>]*class="[^"]*content[^"]*"[^>]*>(.*?)</div>\s*</div>',
        ]:
            match = re.search(pattern, html, re.DOTALL | re.IGNORECASE)
            if match:
                content = match.group(1)
                break
    
    # Fallback
    if not content:
        h_match = re.search(r'</h1>(.*)', html, re.DOTALL | re.IGNORECASE)
        if h_match:
            content = h_match.group(1)
    
    if not content:
        return title, None, featured_image, pub_date, images
    
    # Clean
    content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)
    content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL)
    content = re.sub(r'<nav[^>]*>.*?</nav>', '', content, flags=re.DOTALL)
    content = re.sub(r'<aside[^>]*>.*?</aside>', '', content, flags=re.DOTALL)
    content = re.sub(r'<div[^>]*class="[^"]*(?:share|social|related|comment|author|sidebar|widget|ad-|banner)[^"]*"[^>]*>.*?</div>', '', content, flags=re.DOTALL | re.IGNORECASE)
    
    # Extract paragraphs
    paragraphs = []
    for p_match in re.finditer(r'<p[^>]*>(.*?)</p>', content, re.DOTALL | re.IGNORECASE):
        text = p_match.group(1)
        text = re.sub(r'<br\s*/?>', ' ', text)
        text = re.sub(r'<[^>]+>', '', text).strip()
        text = re.sub(r'\s+', ' ', text)
        if len(text) > 20:
            paragraphs.append(text)
    
    if not paragraphs:
        text = re.sub(r'<[^>]+>', ' ', content)
        text = re.sub(r'\s+', ' ', text).strip()
        if len(text) > 50:
            sentences = text.split('. ')
            chunk = []
            for s in sentences:
                chunk.append(s)
                if len(' '.join(chunk)) > 200:
                    paragraphs.append('. '.join(chunk))
                    chunk = []
            if chunk:
                paragraphs.append('. '.join(chunk))
    
    return title, '\n\n'.join(paragraphs) if paragraphs else None, featured_image, pub_date, images

def load_news():
    with open(NEWS_DATA, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_news(data):
    with open(NEWS_DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_article(aid):
    path = os.path.join(ARTICLES_DIR, f'{aid}.json')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def save_article(article):
    path = os.path.join(ARTICLES_DIR, f'{article["id"]}.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(article, f, ensure_ascii=False, indent=2)

def process_articles():
    """Fetch and translate articles"""
    data = load_news()
    articles = data.get('articles', [])
    print(f"📰 Processing {len(articles)} articles with Google Translate...\n")
    
    updated = 0
    start_time = time.time()
    
    for i, art in enumerate(articles):
        aid = art.get('id', '')
        if not aid:
            continue
        
        # Skip if already has Russian content
        existing = load_article(aid)
        if existing and existing.get('content_ru'):
            articles[i] = existing
            continue
        
        url = art.get('url', '')
        if not url:
            continue
        
        print(f"[{updated+1}] {art.get('title', 'No title')[:60]}...")
        
        # Fetch
        html = fetch_url(url)
        if not html:
            continue
        
        # Extract
        title, content, image, pub_date, images = extract_article_content(html)
        
        if title:
            art['title'] = title
        
        if image:
            art['image'] = image
        
        if images:
            art['images'] = images[:10]  # Save up to 10 images
        
        if pub_date:
            art['pub_date'] = pub_date
        
        if content:
            art['content_en'] = content
            
            # Translate (FAST with Google!)
            print(f"  🔄 Translating ({len(content)} chars)...")
            t_start = time.time()
            
            art['title_ru'] = translate_text(art['title'])
            art['content_ru'] = translate_text(content)
            
            t_time = time.time() - t_start
            print(f"  ✅ Translated in {t_time:.1f}s")
            
            art['fetched_full'] = datetime.now().isoformat()
            save_article(art)
            updated += 1
        else:
            print(f"  ⚠️ No content extracted")
        
        if updated >= 100:
            break
    
    total_time = time.time() - start_time
    save_news(data)
    print(f"\n✅ Updated {updated} articles in {total_time:.1f}s total")

if __name__ == '__main__':
    process_articles()
