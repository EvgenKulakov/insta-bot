import re
from instaloader import Profile


def valid_username(username: str):
    pattern = r'^[a-zA-Z0-9._]{1,30}$'
    return re.match(pattern, username)

def create_profile_text(profile: Profile, story=None):
    start_text = (f'{profile.username}\n\n'
                  f'{profile.full_name}\n'
                  f'{profile.biography}\n\n\n'
                  f'<pre>Комментарий инсташершня:</pre>\n')
    if profile.is_private:
        return (f'{start_text}'
                f'<b>{profile.full_name}</b> - это закрытый профиль. Сторисы для просмотра недоступны')
    if not profile.has_public_story:
        return (f'{start_text}'
                f'У <b>{profile.full_name}</b> в данный момент нет актуальных сторис.\n'
                f'Попробуй прошерстить этот аккаунт позже')
    else:
        if story.itemcount == 1:
            return (f'{start_text}'
                    f'У <b>{profile.full_name}</b> есть одна сторис - '
                    f'выложенная в {story.latest_media_local.strftime("%H:%M:%S")}.\n'
                    f'Я могу анонимно прошерстить этот аккаунт и переслать эту сторис тебе.\n'
                    f'Прошерстить {profile.full_name}?')
        else:
            return (f'{start_text}'
                    f'У <b>{profile.full_name}</b> есть {str(story.itemcount)} сторис '
                    f'(последняя в {story.latest_media_local.strftime("%H:%M:%S")}).\n'
                    f'Я могу анонимно прошерстить этот аккаунт и переслать все сторис тебе.\n'
                    f'Прошерстить {profile.full_name}?')