#!/bin/bash
# MX NEWS - Setup Script
# Установка автоматического агрегатора новостей мотокросса

set -e

echo "🚀 Начало установки MX NEWS..."

# Проверка прав
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  Запустите скрипт с sudo: sudo ./setup.sh"
    exit 1
fi

# Обновление системы
echo "📦 Обновление пакетов..."
apt-get update
apt-get upgrade -y

# Установка зависимостей
echo "📦 Установка зависимостей..."
apt-get install -y python3-pip python3-venv nginx certbot python3-certbot-nginx

# Установка Python библиотек
echo "📦 Установка Python библиотек..."
pip3 install deep-translator beautifulsoup4 requests lxml

# Создание директорий
echo "📁 Создание структуры директорий..."
mkdir -p /var/www/mxnews/{data,js,css}
chown -R www-data:www-data /var/www/mxnews
chmod -R 755 /var/www/mxnews

# Копирование файлов
echo "📄 Копирование файлов..."
cp -r scripts /var/www/mxnews/
cp -r js /var/www/mxnews/
cp -r css /var/www/mxnews/ 2>/dev/null || true

# Настройка Nginx
echo "🌐 Настройка Nginx..."
cp nginx.conf /etc/nginx/sites-available/newsmx
ln -sf /etc/nginx/sites-available/newsmx /etc/nginx/sites-enabled/

# Проверка конфигурации
nginx -t

# Перезагрузка Nginx
echo "🔄 Перезагрузка Nginx..."
systemctl reload nginx

# Настройка SSL (требуется домен)
echo "🔐 Настройка SSL (Let's Encrypt)..."
echo "Для настройки SSL выполните:"
echo "  certbot --nginx -d newsmx.ru -d www.newsmx.ru"
echo ""
echo "Или пропустите этот шаг и настройте позже."

# Настройка cron для автоматического обновления
echo "⏰ Настройка автоматического обновления..."
(crontab -l 2>/dev/null; echo "0 3 * * * cd /var/www/mxnews && python3 scripts/fetch_news.py && python3 scripts/fetch_full.py && python3 scripts/build_site.py >> /var/log/mxnews.log 2>&1") | crontab -

# Создание лог файла
touch /var/log/mxnews.log
chown www-data:www-data /var/log/mxnews.log

# Первоначальная сборка сайта
echo "🏗️  Первоначальная сборка сайта..."
cd /var/www/mxnews
python3 scripts/fetch_news.py
python3 scripts/fetch_full.py
python3 scripts/build_site.py

echo ""
echo "✅ Установка завершена!"
echo ""
echo "📊 Следующие шаги:"
echo "1. Настройте DNS запись для вашего домена"
echo "2. Получите SSL сертификат: certbot --nginx -d ваш-домен.ru"
echo "3. Проверьте сайт: https://ваш-домен.ru"
echo ""
echo "🔄 Автоматическое обновление настроено на 03:00 UTC каждый день"
echo "📝 Логи: /var/log/mxnews.log"
echo "⚙️  Конфигурация Nginx: /etc/nginx/sites-available/newsmx"