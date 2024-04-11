import sqlite3

# Подключение к базе данных (если она существует, она будет открыта, если нет - создастся новая)
conn = sqlite3.connect('/home/evgeniy/PycharmProjects/insta-bot/data/stories.db')

# Создание курсора для выполнения операций с базой данных
cursor = conn.cursor()

# Создание таблицы
cursor.execute('''CREATE TABLE IF NOT EXISTS viewed_stories
                  (id INTEGER PRIMARY KEY, username TEXT, file_name TEXT)''')

# Вставка данных
# cursor.execute("INSERT INTO viewed_stories (username, file_name) VALUES (?, ?)", ('Alice', 'file_ldld'))

# Сохранение изменений
conn.commit()

# Выборка данных
# cursor.execute("SELECT * FROM users")
# rows = cursor.fetchall()
# for row in rows:
#     print(row)

# Закрытие курсора и соединения
cursor.close()
conn.close()