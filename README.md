# Installation
* check runtime.txt
* pip install -r prod.txt
* cp .env.example .env
* edit .env file
* python manage.py migrate
* python manage.py loaddata companies.json
* sudo apt-get install python3.11-dev default-libmysqlclient-dev build-essential
if mysqlclient is not installed successfully

# Deployment
* all steps above
* sudo timedatectl set-timezone America/New_York
* run 'python manage.py crontab add' to add the cron jobs
