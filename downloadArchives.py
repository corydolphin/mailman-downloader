"""
downloadArchives.py: Parses a Mailman Archive site and decodes all of the 
gzipped text archives in mbox format for reading with most popular
email services, or mailbox.py
Usage:   ./downloadArchives.py
#TODO: add inline parameters for urls and for username, password.
#TODO: Thread safety with browser instances? Multiprocessing should speed this up a lot. Investigate

@wcdolphin
"""


import mechanize
import cookielib 
import os, sys
from BeautifulSoup import BeautifulSoup
# Browser
br = mechanize.Browser()

# Use a cookie jar to cache logged-in-ness
cj = cookielib.LWPCookieJar()
br.set_cookiejar(cj)

# Browser options
br.set_handle_equiv(True)
br.set_handle_gzip(True)
br.set_handle_redirect(True)
br.set_handle_referer(True)
br.set_handle_robots(False)

# Follows refresh 0 but not hangs on refresh > 0
br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)

# User-Agent (this is cheating, but good practice)
br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]



def authenticate(mailingListUrl):
    '''
    We first need to authetnicate with mailman and let them give us a cookie 
    that way they know they can trust us!
    '''
    r = br.open(mailingListUrl)
    html = r.read()
    if len([b for b in br.forms()]) == 0:
        return #already authenticated

    br.select_form(nr=0)
    br.form['username'] = 'olinlistarchive@gmail.com'#email
    br.form['password'] = os.environ.get('ARCHIVE_PASSWORD', "You are so scrood")#some funny password
    br.submit()
    

def getArchiveUrls(mailingListUrl):
    '''
    Returns a generator of absolute urls for each of the archives
    '''
    authenticate(mailingListUrl)#first, authenticate with the server

    r = br.open(mailingListUrl)
    html = r.read()
    soup = BeautifulSoup(html)

    if not mailingListUrl[-1] == '/': #need trailing slash for url forming
        mailingListUrl += '/'

    for row in soup.findAll('tr'): # for every table row
        try:
            archiveSource = row.findAll('td')[2].find('a')['href'] #relative URL

            absoluteURL = mailingListUrl + archiveSource #absolute
            yield absoluteURL
        except Exception as inst:
            print inst



def downloadAndDecodeArchive(url,rootDir='',overWrite=True):

    archiveName = url[url.rfind('/')+1:] #get last part of the url path, this is the archive name :-)

    #Check that the directory exists, if not, attempt to create it
    if not os.path.os.path.isdir(rootDir):
        if not os.path.os.path.exists(rootDir):
            try:
                print 'The directory you specified does not exist, attempting to create it'
                os.mkdir(rootDir)
            except Exception as inst:
                print inst

    mboxFileName = os.path.join(rootDir,archiveName.replace('txt.gz','mbox'))

    if not overWrite and os.path.exists(mboxFileName):
        return False
    start = True #this is to_mbox inline to reduce the need to build a new file. #TODO: make method more accessible for generic usage
    with open(mboxFileName,'w') as outMBox:
        for line in br.open(url):
            if line.find("From ") == 0:
                if start:
                    start = False
                else:
                    continue
                line = line.replace(" at ", "@")
            elif line.find("From: ") == 0:
                line = line.replace(" at ", "@")
            elif line.find("Message-ID: ") == 0:
                messageid_stripped = line[line.find('<')+1:line.rfind('>')]
                messageid_stripped = messageid_stripped.replace('@','')
                messageid_stripped = messageid_stripped.replace('.','')
                line = line + "Content-Type: multipart/mixed;boundary=_000_" + messageid_stripped + "_\n"
            elif line.find("-------------- next part --------------") == 0:  # some messages have this crap
                continue
            elif line.find("Skipped content of type text/") == 0:  # some messages have this crap
                continue
            outMBox.write(line)

    return mboxFileName

def getListNameFromUrl(mailingListUrl):
    '''
    Returns the list name inferred from the last path of the url. 
    I.E.   https://lists.fun.edu/mailman/private/helpme/ ==> helpme 
    '''
    if mailingListUrl[-1] == '/':
        return mailingListUrl[mailingListUrl[:-1].rfind('/')+1:-1]
    else:
        return mailingListUrl[mailingListUrl.rfind('/')+1:] 

def downloadAllArchives(mailingListUrl,rootDir,overWrite, printStatus = True):
    for url in getArchiveUrls(mailingListUrl):
        downloadAndDecodeArchive(url,rootDir=rootDir,overWrite=overWrite)
        if printStatus:
            print url

if __name__ == '__main__':
    OVERWRITE = True
    rootDir = './Archives'
    mailingListUrls = ['https://lists.olin.edu/mailman/private/helpme/','https://lists.olin.edu/mailman/private/carpediem/']
    if not os.path.os.path.isdir(rootDir):
        if not os.path.os.path.exists(rootDir):
            try:
                print 'The directory you specified does not exist, attempting to create it'
                os.mkdir(rootDir)
            except Exception as inst:
                print inst

    for url in mailingListUrls:
        downloadAllArchives(url, rootDir=os.path.join(rootDir,getListNameFromUrl(url)), overWrite=OVERWRITE)

