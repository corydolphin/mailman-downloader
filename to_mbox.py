#!/usr/bin/env python
"""
Source: http://lists2.ssc.com/pipermail/linux-list/2006-February/026220.html

Edited: added filtering for the From: field, properly making the property accessible
@wcdolphin

to-mbox.py:  Insert line feeds to create mbox format

Usage:   ./to-mbox.py  infile outfile
"""

def toMbox(archiveFileName,mboxFileName):
    with open(archiveFileName, 'r') as inFile, open(mboxFileName, 'w') as out:
        start = True
        for line in inFile:
            if line.find("From ") == 0:
                if start:
                    start = False
                else:
                    out.write("\n")
                line = line.replace(" at ", "@")
            elif line.find("From: ") == 0:
                line = line.replace(" at ", "@")
            elif line.find("Message-ID: ") == 0:
            	messageid_stripped = line[line.find('<')+1:line.rfind('>')]
            	messageid_stripped = messageid_stripped.replace('@','')
            	messageid_stripped = messageid_stripped.replace('.','')
            	line = line + "Content-Type: multipart/mixed;boundary=_000_" + messageid_stripped + "_\n"
            out.write(line)

        out.close() #python should do this automatically, but just in case
        inFile.close() #python should do this automatically, but just in case

if __name__ == '__main__':
    import sys
    if len(sys.argv) !=3:
        print __doc__
        sys.exit()
    toMbox(sys.argv[1],sys.argv[2])
