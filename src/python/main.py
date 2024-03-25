import instaloader

def download():
    L = instaloader.Instaloader()
    L.login('evgeniy-k123456789@protonmail.com', 'insta54535251')

    # Укажите имя пользователя
    username = 'maga_isma'

    # Скачайте сторис
    L.download_stories(username)

    # Путь к скачанным сторис
    stories_path = f"./{username}/stories"

    # Вывод информации
    print(f"Сторис пользователя {username} успешно скачаны в папку {stories_path}")


download()

