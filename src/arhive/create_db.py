import sqlite3

# Подключение к базе данных (если она существует, она будет открыта, если нет - создастся новая)
conn = sqlite3.connect('/home/evgeniy/PycharmProjects/insta-bot/data/profiles.db')

# Создание курсора для выполнения операций с базой данных
cursor = conn.cursor()

# Создание таблицы
cursor.execute('''CREATE TABLE IF NOT EXISTS success_fail_profiles
                  (id INTEGER PRIMARY KEY, username TEXT UNIQUE ON CONFLICT REPLACE, type TEXT)''')

# Вставка данных
# cursor.execute("INSERT INTO profiles_history (telegram_id, username) VALUES (?, ?)", (123, 'name'))

# Сохранение изменений
conn.commit()

# Выборка данных
# cursor.execute("SELECT * FROM profiles_history")
# rows = cursor.fetchall()
# for row in rows:
#     print(row)

# Закрытие курсора и соединения
cursor.close()
conn.close()