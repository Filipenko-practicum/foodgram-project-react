
# Foodgram!
![example workflow](https://github.com/Filipenko-practicum/foodgram-project-react/actions/workflows/main.yml/badge.svg)
"Продуктовый помощник" - платформа для публикации рецептов.

# Стэк Технологий:
    *Nginx
    *JavaScript
    *Python
    *Django
    *Django Rest Framework
    *Docker
    *Postgres

# Особенности реализации

    *Проект завернут в Docker-контейнеры;
    *Образы foodgram_frontend и foodgram_backend запушены на DockerHub;
    *Реализован workflow c автодеплоем на удаленный сервер.

## Клонируйте репозиторий!
```
git clone git@github.com:Filipenko-practicum/foodgram-project-react
```
# Развертывание на локальном сервере
    *Установите на сервере docker и docker-compose.
    *Создайте файл .env. Шаблон для заполнения файла нахоится в /infra/.env.example.
    *Выполните команду docker-compose up -d --buld.
    *Выполните миграции docker-compose exec backend python manage.py migrate.
    *Создайте суперюзера docker-compose exec backend python manage.py createsuperuser.
    *Соберите статику docker-compose exec backend python manage.py collectstatic --no-input.

# Импорт CSV файлов осуществляется через панель админку
    (http://localhost/admin)

    * Заходиv в раздел Ингредиенты
    * Кликаем на Импорт
    * Выбираем CSV файл
    * Кликаем на загрузку

## Проект состоит из следующих страниц:
    главная
    страница рецепта
    страница пользователя
    страница подписок
    избранное
    список покупок
    создание и редактирование рецепта


# Пользовательские роли

## Права анонимного пользователя:

    Создание аккаунта.
    Просмотр: рецепты на главной, отдельные страницы рецептов, страницы пользователей.
    Фильтрация рецептов по тегам.

## Права авторизованного пользователя (USER):

    Входить в систему под своим логином и паролем.
    Выходить из системы (разлогиниваться).
    Менять свой пароль.
    Создавать/редактировать/удалять собственные рецепты
    Просматривать рецепты на главной.
    Просматривать страницы пользователей.
    Просматривать отдельные страницы рецептов.
    Фильтровать рецепты по тегам.
    Работать с персональным списком избранного: добавлять в него рецепты или удалять их, просматривать свою страницу избранных рецептов.
    Работать с персональным списком покупок: добавлять/удалять любые рецепты, выгружать файл со количеством необходимых ингридиентов для рецептов из списка покупок.
    Подписываться на публикации авторов рецептов и отменять подписку, просматривать свою страницу подписок.

## Права администратора (ADMIN): Все права авторизованного пользователя +

    Изменение пароля любого пользователя,
    Создание/блокирование/удаление аккаунтов пользователей,
    Редактирование/удаление любых рецептов,
    Добавление/удаление/редактирование ингредиентов.
    Добавление/удаление/редактирование тегов.

Администратор Django — те же права, что и у роли Администратор.
Алгоритм регистрации пользователей

## Для добавления нового пользователя нужно отправить POST-запрос на эндпоинт:

POST /api/users/

    В запросе необходимо передать поля:

    email - (string) почта пользователя;
    username - (string) уникальный юзернейм пользователя;
    first_name - (string) имя пользователя;
    last_name - (string) фамилия пользователя;
    password - (string) пароль пользователя.

# Базовые модели проекта!
* Рецепт

    Автор публикации (пользователь).
    Название.
    Картинка.
    Текстовое описание.
    Ингредиенты: продукты для приготовления блюда по рецепту. Множественное поле, выбор из предустановленного списка, с указанием количества и единицы измерения.
    Тег (можно установить несколько тегов на один рецепт, выбор из предустановленных).
    Время приготовления в минутах.

* Тег

    Название.
    Цветовой HEX-код.
    Slug.

* Ингредиент

    Название.
    Количество.
    Единицы измерения.

## Сервис "Список покупок"
Работа со списком покупок доступна авторизованным пользователям. Список покупок может просматривать только его владелец.

# Автор
-Филипенко Александр.