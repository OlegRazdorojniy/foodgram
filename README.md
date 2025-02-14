Foodgram - Продуктовый помощник
## Описание проекта
Foodgram - это веб-приложение, которое позволяет пользователям публиковать рецепты, подписываться на публикации других пользователей, добавлять понравившиеся рецепты в список «Избранное», а также создавать список покупок для выбранных рецептов.
## Технологии
**Backend:**
- Python 3.9
- Django REST framework
- PostgreSQL
- Gunicorn
- Nginx
**Frontend:**
- React
- Node.js 18
**Инфраструктура:**
- Docker
- Docker Compose
- GitHub Actions (CI/CD)
## Установка и запуск
### Предварительные требования
- Docker
- Docker Compose
### Локальный запуск
1. Клонируйте репозиторий:
```bash
git clone git@github.com:OlegRazdorojniy/foodgram.git
cd foodgram
```
2. Создайте файл `.env` в корневой директории проекта и добавьте в него:
```env
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,foodgramio.duckdns.org
```
3. Запустите контейнеры Docker:
```bash
docker compose up -d
```
4. Выполните миграции и соберите статические файлы:
```bash
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py collectstatic
docker compose exec backend cp -r /app/collected_static/. /backend_static/static/
```
5. Загрузите тестовые данные:
```bash
docker compose exec backend python manage.py load_test_data
```
## API Endpoints
- `/api/users/` - управление пользователями
- `/api/tags/` - теги для рецептов
- `/api/ingredients/` - ингредиенты
- `/api/recipes/` - управление рецептами
## Production версия
Рабочая версия проекта доступна по адресу: [https://foodgramio.duckdns.org](https://foodgramio.duckdns.org)
## Авторы
- **Backend и DevOps**:
- **Олег**  
  [GitHub](https://github.com/OlegRazdorojniy)
- **Frontend**: 
- **Яндекс.Практикум**
