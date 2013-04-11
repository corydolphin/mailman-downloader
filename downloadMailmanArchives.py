"""
downloadMailmanArchives.py: Parses a Mailman Archive site and decodes all of the 
gzipped text archives in mbox format for reading with most popular
email services, or mailbox.py
Usage:   ./downloadMailmanArchives.py
#TODO: add inline parameters for urls and for username, password.
#TODO: Thread safety with browser instances? Multiprocessing should speed this up a lot. Investigate

@wcdolphin
"""


import mechanize
import cookielib 
import os, sys, re
from argparse import ArgumentParser
from BeautifulSoup import BeautifulSoup
import urlparse
import traceback


def authenticate(br, mailingListUrl, username, password):
    '''
    We first need to authetnicate with mailman and let them give us a cookie 
    that way they know they can trust us!
    '''
    r = br.open(mailingListUrl)
    html = r.read()
    if len([b for b in br.forms()]) == 0:
        return #already authenticated


    br.select_form(nr=0)
    br.form['username'] = username
    br.form['password'] = password
    resp = br.submit()
    return resp.read().find("Authorization failed") == -1


def getArchiveUrls(br, mailingListUrl):
    '''
    Returns a generator of absolute urls for each of the archives
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
                if line.find("From ") == 0:
                    line = line.replace(" at ", "@")
                elif line.find("From: ") == 0:
                    line = line.replace(" at ", "@")
                elif line.find("Message-ID: ") == 0:
                    messageid_stripped = line[line.find('<')+1:line.rfind('>')]
                    messageid_stripped = messageid_stripped.replace('@','')
                    messageid_stripped = messageid_stripped.replace('.','')
                    messageid_stripped = messageid_stripped[0:55]
                    if lineNum +2 < len(lines) and lines[lineNum+2].find('--') ==0:
                        boundary = lines[lineNum+2][2:]
                        line = line +"\n" + "Content-Type: multipart/mixed;boundary=\"" + boundary + '"'
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

def downloadAllArchives(mailingListUrl,args):
    # Browser
    br = mechanize.Browser()
    cj = cookielib.LWPCookieJar()
    br.set_cookiejar(cj)
    br.set_handle_equiv(True)
    br.set_handle_gzip(True)
    br.set_handle_redirect(True)
    br.set_handle_referer(True)
    br.set_handle_robots(False)
    br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
    br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]

    listName = getListNameFromUrl(mailingListUrl)
    if args.password != None and args.username != None:
        success = authenticate(br, mailingListUrl, args.username, args.password) #first, authenticate with the server
        if not success:
            print >> sys.stderr, "Failed to authenticate with List:'%s', check username and password" % listName
            return 1

    rootDir = os.path.join(args.dest,listName)

    for url in getArchiveUrls(br, mailingListUrl):
        archiveName = url[url.find(listName):]
        try:
            overWrote, cached = downloadAndDecodeArchive(br, url, rootDir=rootDir, overWrite=args.force)
            if cached:
                print "Found cached version, skipping '%s'" % archiveName
            else:
                print "Downloaded" + [""," and overwrote"][overWrote] + " '%s'" % archiveName

        except Exception, e:
            print  >> sys.stderr, "Failed to download '%s'" % archiveName
            return 1
    return 0



class MyArgumentParser(ArgumentParser):
    def __init__(self):
        usage = "Downloads and decodes Mailman archives into .mbox files"
        ArgumentParser.__init__(self, usage,
                              version="Mailman Downloader 1.0")
        self.add_argument("archive_root_url", nargs='+', help="Root url for archive")
        self.add_argument("--username", help="login name [default: empty]")
        self.add_argument("--password", help="login password")
        self.add_argument("--dest", help="Destination for archives", default = './archives')
        self.add_argument("--force", help="Overwrite files stored locally?", action = 'store_const', const=True)

def main(args):
    '''
    See ArgumentsParser for argument list
    '''
    if not os.path.os.path.isdir(args.dest):
        if not os.path.os.path.exists(args.dest):
            try:
                print 'The directory you specified does not exist, attempting to create it'
                os.mkdir(args.dest)
            except Exception, e :
                print >>sys.stderr, "An unknown error has occurred: ", e

    result = 0
    for url in args.archive_root_url:
        res = downloadAllArchives(url, args)
        if res != 0:
            print >>sys.stderr, "An error occured while downloading '%s'" % getListNameFromUrl(url)
        result += res
    return result

if __name__ == '__main__':
    try:
        # Parse arguments
        parser = MyArgumentParser()
        args = parser.parse_args()

        sys.exit(main(args))

    except Exception, e:
        print >>sys.stderr, "An unknown error has occurred: "
        traceback.print_exc()

