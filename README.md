# MX NEWS - Мотокросс новости на русском

Автоматический агрегатор новостей мотокросса с переводом на русский язык.

## 🚀 Особенности

- **Автоматический сбор** новостей из англоязычных источников
- **Машинный перевод** на русский язык (Google Translate API)
- **Статический сайт** - быстрая загрузка, минимальные требования
- **Сортировка по дате** - свежие новости сверху
- **Автоматическое обновление** по расписанию (cron)

## 📁 Структура проекта

```
mxnews/
├── scripts/                    # Скрипты обновления
│   ├── fetch_news.py          # Сбор новостей из источников
│   ├── fetch_full.py          # Полное обновление контента
│   └── build_site.py          # Генерация HTML страниц
├── js/                        # JavaScript файлы
│   └── main.js               # Основной JS + счётчик посещений
├── css/                       # Стили
│   └── style.css             # Основные стили

├── data/                      # Данные (генерируется)
│   └── news.json             # База статей
├── nginx.conf                # Конфигурация Nginx
├── setup.sh                  # Скрипт установки
├── requirements.txt          # Зависимости Python
└── README.md                 # Эта документация
```

## 🛠️ Установка

### 1. Клонирование и настройка
```bash
git clone https://github.com/wohan/mxnews.git
cd mxnews

# Установка зависимостей
pip3 install -r requirements.txt

# Настройка директорий
sudo mkdir -p /var/www/mxnews
sudo chown -R $USER:$USER /var/www/mxnews
cp -r * /var/www/mxnews/
```

### 2. Настройка Nginx
```bash
# Копирование конфигурации
sudo cp nginx.conf /etc/nginx/sites-available/newsmx
sudo ln -sf /etc/nginx/sites-available/newsmx /etc/nginx/sites-enabled/

# Проверка и перезагрузка
sudo nginx -t
sudo systemctl reload nginx
```

### 3. SSL сертификаты (Let's Encrypt)
```bash
sudo certbot --nginx -d newsmx.ru -d www.newsmx.ru
```

### 4. Настройка cron для автоматического обновления
```bash
# Добавить в crontab
crontab -e

# Добавить строку:
0 3 * * * cd /var/www/mxnews && python3 scripts/fetch_news.py && python3 scripts/fetch_full.py && python3 scripts/build_site.py >> /var/log/mxnews.log 2>&1
```

## 🔧 Скрипты обновления

### `scripts/fetch_news.py`
Сбор новостей из источников:
- Motocross Action Magazine
- RacerX Online
- MXGP официальный сайт
- Supercross новости

### `scripts/fetch_full.py`
Полное обновление контента:
- Перевод заголовков и текста
- Извлечение изображений
- Сохранение в JSON базу

### `scripts/build_site.py`
Генерация HTML страниц:
- Главная страница
- Разделы (MXGP, Supercross, Техника и др.)
- Страницы статей
- Sitemap.xml



## 🌐 Источники новостей

1. **Motocross Action Magazine** - обзоры техники, тесты
2. **RacerX Online** - новости Supercross и MXGP
3. **MXGP Official** - чемпионат мира по мотокроссу
4. **AMA Supercross** - американский суперкросс
5. **GNCC Racing** - кросс-кантри эндуро
6. **FIM Rally** - ралли-рейды

## ⚙️ Требования

- **Python 3.8+** с библиотеками:
  - `deep-translator` (Google Translate)
  - `beautifulsoup4` (парсинг HTML)
  - `requests` (HTTP запросы)
- **Nginx** (веб-сервер)
- **Cron** (для автоматического обновления)

## 🔄 Ручное обновление

```bash
cd /var/www/mxnews

# Сбор новостей
python3 scripts/fetch_news.py

# Полное обновление
python3 scripts/fetch_full.py

# Пересборка сайта
python3 scripts/build_site.py
```

## 📝 Лицензия

MIT License - свободное использование и модификация.

## 👤 Автор

**Владимир Зыков** (@wohan)
- GitHub: https://github.com/wohan
- Сайт: https://newsmx.ru

## 🤝 Вклад в проект

1. Форкните репозиторий
2. Создайте ветку для новой функции
3. Внесите изменения
4. Отправьте Pull Request

---

**Последнее обновление:** 20 марта 2026  
**Версия:** 1.0.0