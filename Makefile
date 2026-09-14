.PHONY: install migrate seed run test shell superuser collectstatic docker-up docker-down

install:
	python -m venv venv
	venv\Scripts\activate && pip install -r requirements.txt

migrate:
	python manage.py migrate

seed:
	python manage.py seed_demo

run:
	python manage.py runserver

test:
	python manage.py test

shell:
	python manage.py shell

superuser:
	python manage.py createsuperuser

collectstatic:
	python manage.py collectstatic --noinput

docker-up:
	docker compose up --build

docker-down:
	docker compose down
