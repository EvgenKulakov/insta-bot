import os

target_folder = '/home/evgeniy/PycharmProjects/insta-bot/cache/morgen'

if not os.path.exists(target_folder):
    os.makedirs(target_folder)

file_path = os.path.join(target_folder, "some.jpg")
print(file_path)

with open(file_path + '.temp', 'wb') as file:
    print('all good')