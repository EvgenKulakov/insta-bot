import instaloader
from instaloader import Profile


def download():
    USER = 'svetlanabeautifulmorning'
    TOKEN = '/home/evgeniy/PycharmProjects/insta-bot/session-token'
    L = instaloader.Instaloader()
    L.load_session_from_file(USER, TOKEN)

    username = 'anichkina_a'
    profile = Profile.from_username(L.context, username)

    # L.download_stories(userids=[profile.userid], filename_target='cache')
    # stories = L.get_stories([profile.userid])
    #
    # for story in stories:
    #     print(story)
    #     print(dir(story))
    #     story_items = story.get_items()
    #     for item in story_items:
    #         print(item)
    #         print(dir(item))
    #         L.download_storyitem(item, f'cache.{username}')
    #     print('****************************************')

    posts = profile.get_posts()
    first_post = next(posts)
    print(first_post)
    print(dir(first_post))
    print('*********************************')

    L.download_post(first_post, f'cache.{username}')

    print("Сторис загружены успешно!")


download()

