from app import create_app
app = create_app()   # usado por gunicorn/uwsgi; local: FLASK_APP=app:create_app
