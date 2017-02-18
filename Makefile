PROD_PATH=/srv/python-slackbot

install:
	sudo rsync -av --progress . $(PROD_PATH) --exclude-from 'exclude-list'

install_venv:
	sudo $(PROD_PATH)/scripts/build_venv.sh $(PROD_PATH) $(PROD_PATH)/requirements.txt
