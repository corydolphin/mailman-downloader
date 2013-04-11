import os
from downloadMailmanArchives import main
class Struct:
    def __init__(self, **entries): 
        self.__dict__.update(entries)

if __name__ == '__main__':
    args = {
    'archive_root_url': ['https://lists.olin.edu/mailman/private/carpediem/', 'https://lists.olin.edu/mailman/private/helpme/'],
    'password' : os.environ.get('ARCHIVE_LOGIN', "fail"),
    'username' : os.environ.get('ARCHIVE_PASS', "fail"),
    'force' : True,
    'dest' : './archives'
    }
    main(Struct(**args))

