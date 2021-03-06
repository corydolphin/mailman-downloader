# Mailman Downloader

This repository holds a collection of scripts and tools to access, parse and manage Mailman list archives. In particular, downloading the archives, parsing to mbox files and uploading over IMAP to Gmail.

`mailman_downloader.py` holds the main script which can be used either as a module (via calling the `download` method, or any of the other documented and exposed methods), or simply as a script from the commandline.

```
usage: Downloads and decodes Mailman archives into .mbox files
       [-h] [-v] [--username USERNAME] [--password PASSWORD] [--dest DEST]
       [--force]
       list_archive_urls [list_archive_urls ...]

positional arguments:
  list_archive_urls    Root url(s) for archive

optional arguments:
  -h, --help           show this help message and exit
  -v, --version        show program's version number and exit
  --username USERNAME  login name [default: empty]
  --password PASSWORD  login password
  --dest DEST          Destination for archives
  --force              Flag to overwrites files stored locally
```

# Gmail Uploader

`gmail_uploader.py` contains a relatively thin wrapper around `imap_upload`,a library which was slightly modified and improved to be more easily used as an external module [source](http://imap-upload.sourceforge.net/).

```
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
```

# Dependencies

The script has a number of dependencies: BeautifulSoup for parsing HTML, Mechanize for simulating a browser for login (should be refactored and replaced with requests, soon).

You can install these dependencies using pip:

```
pip install -r requirements.txt
```
