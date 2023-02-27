_SUCCESS := "\033[32m[%s]\033[0m %s\n" # Green text for "printf"
_DANGER := "\033[31m[%s]\033[0m %s\n" # Red text for "printf"

dummy:
	@echo Dont run without arguments!

install:
	poetry install

admin:
	python manage.py createsuperuser --username=swasher --email=mr.swasher@gmail.com --skip-checks;

migrations:
    # возможно тут надо указать имена apps после makemigrations
	python manage.py makemigrations

migrate:
    # нужно указывать --run-syncdb для первой миграции, иначе не создаются базы
	python manage.py migrate

cleardb:
	rm -rf inventory/migrations/*
	docker compose down
	docker volume prune --force
	docker compose up -d
	sleep 2
	python manage.py makemigrations inventory
	python manage.py migrate --run-syncdb
	python manage.py loaddata */fixtures/*.json
    # python manage.py createsuperuser --username=swasher --email=mr.swasher@gmail.com; becouse it's already in fixtures

load_fixtures:
	python manage.py loaddata */fixtures/*.json

save_fixtures:
	@read  -p "Are you sure? IT WILL DELETE ALL EXISTING FIXTURES!!! [y/N] " ans && ans=$${ans:-N} ; \
    if [ $${ans} = y ] || [ $${ans} = Y ]; then \
        printf $(_SUCCESS) "YES" ; \
		python -Xutf8 manage.py dumpdata APP.DB --indent 4 --output APP/fixtures/DB.json ; \
    else \
        printf $(_DANGER) "NO" ; \
    fi
	@echo 'Next steps...'



build:
	docker compose up -d  --build

up:
	docker compose up -d

down:
	docker compose down

make_requirements:
	pipenv run pip freeze > requirements.txt

ssh:
	docker exec -it sandglass_db_1 bash

heroku-reset-db:
	heroku pg:reset
	heroku run python manage.py migrate
	heroku run python manage.py createsuperuser --username=swasher --email=mr.swasher@gmail.com
	heroku run python manage.py collectstatic

restore:
	cat latest.dump | docker exec -i sith-db-1 pg_restore --verbose --clean --no-acl --no-owner -h localhost -U postgres -d postgres

