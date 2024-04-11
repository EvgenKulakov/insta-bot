from typing import List

import instagrapi
from instagrapi.types import User


def create_user_text(user: User, stories: List[instagrapi.types.Story]) -> str:
    start_text = (f'{user.username}\n\n'
                  f'{user.full_name}\n'
                  f'{user.biography}\n\n\n'
                  f'<pre>Комментарий инсташершня:</pre>\n')
    if user.is_private:
        return (f'{start_text}'
                f'<b>{user.full_name}</b> - это закрытый профиль. Сторисы недоступны для просмотра')
    if len(stories) == 0:
        return (f'{start_text}'
                f'У <b>{user.full_name}</b> в данный момент нет актуальных сторис.\n'
                f'Попробуй прошерстить этот аккаунт позже')
    else:
        if len(stories) == 1:
            return (f'{start_text}'
                    f'У <b>{user.full_name}</b> есть одна сторис - '
                    f'выложенная в {stories[0].taken_at.strftime("%H:%M:%S")}.\n'
                    f'Я могу анонимно прошерстить этот аккаунт и переслать эту сторис тебе.\n'
                    f'Прошерстить {user.full_name}?')
        else:
            return (f'{start_text}'
                    f'У <b>{user.full_name}</b> есть {str(len(stories))} сторис '
                    f'(последняя в {stories[-1].taken_at.strftime("%H:%M:%S")}).\n'
                    f'Я могу анонимно прошерстить этот аккаунт и переслать все сторис тебе.\n'
                    f'Прошерстить {user.full_name}?')