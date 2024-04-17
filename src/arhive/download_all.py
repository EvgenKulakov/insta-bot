from instaloader import Instaloader


def download():
    loader = Instaloader()
    loader.download_profile('username')

download()