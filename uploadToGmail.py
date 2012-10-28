from imap_upload import *
import sys
import mailbox
import os

if __name__ == '__main__':
	options = {'box': 'INBOX', 'retry': 3,'ssl': True, 'host': 'imap.gmail.com',
	'user': 'olinlistarchive@gmail.com', 'error': None,
	'password': 'PASSWORD', 'port': 993,
	'time_fields': ['from', 'received', 'date']}


	root_dir = './Archives/helpme'

	err = options.pop("error")
	time_fields = options.pop("time_fields")

	# Connect to the server and login
	print >>sys.stderr, \
		  "Connecting to %s:%s." % (options["host"], options["port"])
	uploader = IMAPUploader(**options)
	uploader.open()
	# Prepare source and error mbox

	for filName in os.listdir(root_dir):
		src = os.path.join(root_dir,filName)
		
		src = mailbox.mbox(src, create=False)
		if err:
			err = mailbox.mbox(err)
		# Upload
		print >>sys.stderr, "Uploading..."
		upload(uploader, src, err, time_fields)
		