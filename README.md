 ## Сайт Foodgram - Продуктовый помощник

 ![workflow](https://github.com/rest2011/foodgram-project-react/actions/workflows/main.yml/badge.svg?event=push)

---
 На сайте "Продуктовый помощник" (сайт-сборник рецептов) доступна регистрация пользователей, гости могут просматривать рецепты, после авторизации доступно добавление рецептов, редактирование и удаление своих рецептов. Авторизованные пользователи могут добавлять любые рецепты в свое избранное, список покупок (который можно скачать для похода в магазин), подписываться на других авторов.

 **Технологии:**
Python 3.9, Django 3.2, DRF 3.12, React, Docker, Nginx, Postgresql, Github Actions.

 **Запуск проекта локально**

 ```bash
git clone <project>
cd foodgram-project-react/
# создайте и заполните файл окружения .env необходимыми данными:
# POSTGRES_DB=foodgram
# POSTGRES_USER=foodgram_user
# POSTGRES_PASSWORD=foodgram_password
# DB_NAME=foodgram
# DB_HOST=db
# DB_PORT=5432
# SECRET_KEY=<ваш секретный ключ из settings.py>
# DEBUG=True
# ALLOWED_HOSTS=<хосты, разделенные "пробелом">
# DB_ENGINE=django.db.backends.postgresql
 ```

***Команды для Docker***
 ```bash
docker compose up -d
# запускаем миграции и сборку статики
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py collectstatic --noinput
# БД можно заполнить предустановленными тегами и ингредиентами
docker-compose exec backend python manage.py tags_import
docker-compose exec backend python manage.py ingredients_import
# копируем статику
docker-compose exec backend cp -r collect_static/. ../static_backend/static_backend/
```
***Использование сайта***

```bash
# Сайт доступен по адресу
http://localhost/
```
На сайте регистрируемся и авторизуемся. Становится доступен весь функционал - по добавлению рецептов, редактированию, удалению своих блюд. Появляется страница "Избранное" и "Список покупок", можно подписаться на любого автора и просматривать его рецепты.

### Автор
Ринат Хаматьяров (https://github.com/rest2011)

Сайт доступен по адресу:
https://restfood.sytes.net/ (158.160.0.4)

Данные для доступа в админку:
логин - admin
пароль - user1111
