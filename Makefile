install:
	rsync -av --progress . /srv/python-slackbot/ --exclude-from 'exclude-list'
