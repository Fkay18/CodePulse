web: python manage.py collectstatic --noinput && python manage.py migrate --noinput && gunicorn codepulse.wsgi:application --bind 0.0.0.0:$PORT
