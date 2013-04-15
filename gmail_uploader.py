#!/usr/bin/python
"""
gmail_uploader.py:
Uploads one or more mbox archives to Gmail over imap.

usage: Uploads mbox files to Gmail [-h] [-v] [--retries RETRIES] [--v]
                                   root_dir gmail_address password
                                   destinationFolder

positional arguments:
  root_dir           Root directory for mbox archives
  gmail_address      Gmail email address
  password           Gmail password
  destinationFolder  Destination Gmail folder to upload archives to

optional arguments:
  -h, --help         show this help message and exit
  -v, --version      show program's version number and exit
  --retries RETRIES  Number of times to retry upload
  --v                Verbose output


Written by @wcdolphin
"""
__version__ = "1.0"
from imap_upload import *
import sys
import mailbox
import os
import traceback
from argparse import ArgumentParser



class MyArgumentParser(ArgumentParser):
    def __init__(self):
        usage = "Uploads mbox files to Gmail"
        ArgumentParser.__init__(self, usage,
                              version="Gmail Uploader %s" % __version__)
        self.add_argument("root_dir",  
                          help="Root directory for mbox archives")
        self.add_argument("gmail_address", help="Gmail email address")
        self.add_argument("password", help="Gmail password")
        self.add_argument("destinationFolder", help=("Destination Gmail folder" 
            " to upload archives to"))
        self.add_argument("--retries", help="Number of times to retry upload", 
             default=3)

        self.add_argument("--v", help="Verbose output", 
            action='store_const', const=True, default=False)


def uploadToGmail(root_dir, gmail_address, password, destinationFolder, v,
                  retries=3):
    '''
    Uploads all mailbox archives found in root_dir to gmail, using the
    specified `gmail_address`, and `password` to authenticate. Will upload to
    the folder `destinationFolder`. `v` turns on verbose mode.
    '''

    uploader = IMAPUploader("imap.gmail.com", 993, True, destinationFolder,
                            gmail_address, password, retries)
    uploader.open()
    for filName in os.listdir(root_dir):
        srcPath = os.path.join(root_dir,filName)

        src = mailbox.mbox(srcPath, create=False)
        print  "Uploading...%s" % srcPath
        uploader.uploadMbox(src, None,  time_fields=['from', 'received', 'date'],
         showProgess=v)

def main():
    try:
        # Parse arguments
        parser = MyArgumentParser()
        args = parser.parse_args()
        uploadToGmail(**args.__dict__)
    except Exception, e:
        print >>sys.stderr, "An unknown error has occurred: "
        traceback.print_exc()

if __name__ == '__main__':
    main()







