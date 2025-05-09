.PHONY: migrations
migrations: 
	python3 manage.py makemigrations

.PHONY: migrate
migrate: 
	python3 manage.py migrate

.PHONY: runserver
runserver: 
	python3 manage.py runserver 8001

.PHONY: superuser
superuser: 
	python3 manage.py createsuperuser

.PHONY: pyshell
pyshell: 
	python3 manage.py shell

.PHONY: celery
celery:
	celery -A pulcity worker --loglevel=info

.PHONY: dbshell
dbshell:
	python3 manage.py dbshell

.	PHONY: apitest
apitest:
	python3 manage.py test