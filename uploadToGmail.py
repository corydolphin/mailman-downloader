from imap_upload import *
import sys
import mailbox
import os

if __name__ == '__main__':
	options = {'box': 'carpediem', 'retry': 3,'ssl': True, 'host': 'imap.gmail.com',
	'user': 'olinlistarchive@gmail.com', 'error': None,
	'password': os.environ.get('ARCHIVE_PASSWORD', "You are so scrood"), 'port': 993,
	'time_fields': ['from', 'received', 'date']}

	root_dir = './Archives/carpediem'

	err = options.pop("error")
	time_fields = options.pop("time_fields")

	# Connect to the server and login
	print "Connecting to %s:%s." % (options["host"], options["port"])
	uploader = IMAPUploader(**options)
	uploader.open()
	# Prepare source and error mbox

	for filName in os.listdir(root_dir):
		srcPath = os.path.join(root_dir,filName)

		src = mailbox.mbox(srcPath, create=False)
		if err:
			err = mailbox.mbox(err)
		# Upload
		print  "Uploading...%s" % srcPath
		upload(uploader, src, err, time_fields)
