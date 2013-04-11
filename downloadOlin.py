import os
from mailman_downloader import download
if __name__ == '__main__':

    download(['https://lists.olin.edu/mailman/private/carpediem/', 'https://lists.olin.edu/mailman/private/helpme/'],
        password=os.environ.get('ARCHIVE_LOGIN', "fail"),
        username=os.environ.get('ARCHIVE_PASS', "fail"),
        force=True,
        dest='./archives'
    )
