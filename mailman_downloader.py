#!/usr/bin/python
"""
mailman_downloader.py: 
Parses a Mailman Archive site and decodes all gzipped text archives into mbox
format for reading with most popular email services, or mailbox.py

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
  --force       

Written by @wcdolphin
"""
__version__ = "1.0"
import mechanize
import cookielib 
import os, sys, re
from argparse import ArgumentParser
from BeautifulSoup import BeautifulSoup
import urlparse
import traceback

class AuthorizationException(Exception):
    pass

class MyArgumentParser(ArgumentParser):
    def __init__(self):
        usage = "Downloads and decodes Mailman archives into .mbox files"
        ArgumentParser.__init__(self, usage,
                              version="Mailman Downloader %s" % __version__)
        self.add_argument("list_archive_urls", nargs='+', 
                          help="Root url(s) for archive")
        self.add_argument("--username", help="login name [default: empty]")
        self.add_argument("--password", help="login password")
        self.add_argument("--dest", help="Destination for archives",
                          default = './archives')
        self.add_argument("--force",
                          help="Flag to overwrites files stored locally", 
                          action = 'store_const', const=True)

def authenticate(br, mailingListUrl, username, password):
    '''
    Authenticates a Mechanize::Browser instance with the Mailman server
    for at `mailingListUrl` using `username` and `password`
    The returned cookie is stored transparently by mechanize in a cookierjar
    '''
    r = br.open(mailingListUrl)
    html = r.read()
    if len([b for b in br.forms()]) == 0:
        return #already authenticated

    br.select_form(nr=0)
    br.form['username'] = username
    br.form['password'] = password
    resp = br.submit()
    if resp.read().find("Authorization failed") != -1:
        raise AuthorizationException("Authorization failed")


def getArchiveUrls(br, mailingListUrl):
    '''
    Returns a generator of absolute urls for each of the archives found
    at the `mailingListUrl`
    '''

    r = br.open(mailingListUrl)
    html = r.read()
    soup = BeautifulSoup(html)


    if not mailingListUrl[-1] == '/': #need trailing slash for url forming
        mailingListUrl += '/'

    for row in soup.findAll('tr')[1:]: # skip first row for every table row
        try:
            archiveSource = row.findAll('td')[2].find('a')['href'] #relative URL

            absoluteURL = mailingListUrl + archiveSource #absolute
            yield absoluteURL
        except Exception, e :
            traceback.print_exc()


def downloadAndDecodeArchive(br, url, rootDir='',overWrite=True):
    '''
    Downloads and decodes a mailman archive (txt.gz) found at url,
    decoding it and saving it to rootDir. If overWrite = True, and
    a file with the same name exists, the original will be clobbered.

    returns: tuple(overwrote, cached)

    '''
    archiveName = url[url.rfind('/')+1:] #get last part of the url path, this is the archive name :-)
    overWrote = False
    #Check that the directory exists, if not, attempt to create it
    if not os.path.os.path.isdir(rootDir):
        if not os.path.os.path.exists(rootDir):
            try:
                print 'The directory you specified does not exist, attempting to create it'
                os.mkdir(rootDir)
            except Exception, e :
                traceback.print_exc()
                raise
    message_id_reg = re.compile("[^a-zA-Z0-9_]")  #multipart boundary is message id with only alphanum and underscores
    mboxFileName = os.path.join(rootDir,archiveName.replace('txt.gz','mbox'))


    if os.path.exists(mboxFileName):
        if not overWrite:
            return False, True
        else:
            overWrote = True

    try:
        start = True #this is to_mbox inline to reduce the need to build a new file. #TODO: make method more accessible for generic usage
        with open(mboxFileName,'w') as outMBox:
            resp = br.open(url)  # get response object
            lines = resp.read().splitlines()  # we actually need the full file, must buffer into memory. 
            lineNum = 0
            while lineNum < len(lines):
                line = lines[lineNum]
                if line.find("From ") == 0: #There are multiple From fields
                    line = line.replace(" at ", "@")
                elif line.find("From: ") == 0: #There are multiple From fields
                    line = line.replace(" at ", "@")
                elif line.find("Message-ID: ") == 0:
                    messageid_stripped = line[line.find('<')+1:line.rfind('>')]
                    messageid_stripped = messageid_stripped.replace('@','')
                    messageid_stripped = messageid_stripped.replace('.','')
                    messageid_stripped = messageid_stripped[0:55]
                    if lineNum +2 < len(lines) and lines[lineNum+2].find('--') ==0:
                        boundary = lines[lineNum+2][2:] #readahead and find the
                        line = line +"\n" + 'Content-Type: multipart/mixed;boundary="%s"' % boundary
                    else:
                        pass
                elif line.find("-------------- next part --------------") == 0:  # some messages have this crap
                    line = None
                elif line.find("Skipped content of type") == 0:  # some messages have this crap
                    line = None
                if line != None:
                    outMBox.write(line + "\n")
                lineNum +=1
        return overWrote, False

    except Exception, e:
        traceback.print_exc()
        raise
def getListNameFromUrl(mailingListUrl):
    '''
    Returns the list name inferred from the last path of the url. 
    Example:   https://mail.mozilla.org/pipermail/rust-dev/ ==> rust-dev 
    '''
    if mailingListUrl[-1] == '/':
        return mailingListUrl[mailingListUrl[:-1].rfind('/')+1:-1]
    else:
        return mailingListUrl[mailingListUrl.rfind('/')+1:] 

def downloadList(mailingListUrl, username=None, password=None, dest=None, force=True):
    '''
    A main entrypoint for this module. Downloads all of the archives for a particular mailinglist specified, 
    decoding all archives and storing them as .mbox files in the dest directory
    under a subdirectory for the particular mailing list.
    Consider this the major entry point. It also is the only function
    which holds any state, in the form of a mechanize.Browser instance
    '''

    br = mechanize.Browser()
    cj = cookielib.LWPCookieJar()
    br.set_cookiejar(cj)
    br.set_handle_equiv(True)
    br.set_handle_gzip(True) #we get gzip decompression for free!
    br.set_handle_redirect(True)
    br.set_handle_referer(True)
    br.set_handle_robots(False)
    br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
    br.addheaders = [('User-agent', ('Mozilla/5.0 (X11; U; Linux i686; en-US;'
                    ' rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox'
                    '/3.0.1')
                    )]

    listName = getListNameFromUrl(mailingListUrl)
    if password != None and username != None: #Authentication required
        try:
            authenticate(br, mailingListUrl, username, password) #first, authenticate with the server
        except AuthorizationException, ae:
            print >> sys.stderr, "Failed to authenticate with List:'%s', check username and password" % listName
            raise
        except Exception,e:
            print >> sys.stderr, "Failed to authenticate with List:'%s'" % listName
            traceback.print_exc()
            raise


    rootDir = os.path.join(dest,listName)

    for url in getArchiveUrls(br, mailingListUrl):
        archiveName = url[url.find(listName):]
        try:
            overWrote, cached = downloadAndDecodeArchive(br, url, 
                                                rootDir=rootDir,
                                                overWrite=force)
            if cached:
                print "Found cached version, skipping '%s'" % archiveName
            else:
                print "Downloaded" + [""," and overwrote"][overWrote] + " '%s'" % archiveName

        except Exception, e:
            print  >> sys.stderr, "Failed to download '%s'" % archiveName
            raise


def download(list_archive_urls, username=None, password=None, dest=None, force=True):
    '''
    This function will download all archives of all mailing lists specified
    in the list_archive_urls list, with username and password used for 
    authenticating with Mailman.

    Argument list:
        :list_archive_urls: the list of mailing list urls 
        :username: the username to be used for authenticating
        :password: the password to be used for authenticating
        :dest: the destination directory for downloaded archives
        :force: flag to overwrite files found with the same name.
    '''

    if not os.path.os.path.isdir(dest):
        if not os.path.os.path.exists(dest):
            try:
                print ('The directory you specified does not exist,'
                       'attempting to create it')
                os.mkdir(dest)
            except Exception, e :
                print >>sys.stderr, "An unknown error has occurred: "
                print_exc
    for list_archive_url in list_archive_urls:
        try:
            downloadList(list_archive_url, username=username, 
                        password=password, dest=dest, force=force)
        except Exception, e:
             print >> sys.stderr, "An error occured while downloading '%s'" % (
                                   getListNameFromUrl(list_archive_url))
             traceback.print_exc()


def main():
    '''
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

    Example:
    python mailman_downloader.py http://mail.python.org/pipermail/python-dev/
    '''
    try:
        # Parse arguments
        parser = MyArgumentParser()
        args = parser.parse_args()
        download(args.list_archive_urls, username=args.username,
                 password=args.password, dest=args.dest, force=args.force)

    except Exception, e:
        print >>sys.stderr, "An unknown error has occurred: "
        traceback.print_exc()


if __name__ == '__main__':
    main()

