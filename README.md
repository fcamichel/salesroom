# SalesRoom

Demo project using [Channels](http://channels.readthedocs.org/)

## Installation

**Manual installation**

Make a new virtualenv for the project, and run:

`pip install -r requirements.txt`

Then, you'll need Redis running locally; the settings are configured to point to `localhost`, port `6379`,  but you can 
change this in the `CHANNEL_LAYERS` setting in `settings.py`.

Finally, run:

`python manage.py migrate`
`python manage.py runserver`

**Docker installation**

Run the app:

`docker-compose up -d`

The app will now be running on: {your-docker-ip}:8000

**Note:** You will need to prefix `python manage.py` commands with: `docker-compose run --rm web` .
e.g.: `docker-compose run --rm web python manage.py createsuperuser`

Finally, run:

`docker-compose run --rm web python manage.py migrate`