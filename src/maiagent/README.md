# maiagent

HW

[![Built with Cookiecutter Django](https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg?logo=cookiecutter)](https://github.com/cookiecutter/cookiecutter-django/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

License: MIT

## Settings

Moved to [settings](https://cookiecutter-django.readthedocs.io/en/latest/1-getting-started/settings.html).

## Development Setup

### Prerequisites

- Docker and Docker Compose
- Node.js (version 24.6 or compatible)
- npm

### Running the Application

This project requires running both Django backend and webpack dev server for proper static file serving.

#### 1. Start Django Backend Services

```bash
cd src/maiagent
docker compose -f docker-compose.local.yml up -d
```

This starts:
- Django web server (http://localhost:8000)
- PostgreSQL database
- Redis cache
- Elasticsearch
- Celery worker and beat

#### 2. Start Webpack Dev Server

```bash
cd src/maiagent
npm install  # Install dependencies (first time only)
npm run dev  # Start webpack dev server
```

The webpack dev server runs on http://localhost:3000 and serves static files (CSS/JS) to Django.

#### 3. Access the Application

- Main application: http://localhost:8000
- Django admin: http://localhost:8000/admin/

**Important**: Both services must be running simultaneously. Django templates load static files from the webpack dev server at localhost:3000.

### Troubleshooting

If you see `net::ERR_CONNECTION_REFUSED` errors for static files:
1. Ensure webpack dev server is running: `npm run dev`
2. Check that port 3000 is available and not blocked by firewall
3. Verify Django settings point to `http://localhost:3000/static/webpack_bundles/`

## Basic Commands

### Setting Up Your Users

- To create a **normal user account**, just go to Sign Up and fill out the form. Once you submit it, you'll see a "Verify Your E-mail Address" page. Go to your console to see a simulated email verification message. Copy the link into your browser. Now the user's email should be verified and ready to go.

- To create a **superuser account**, use this command:

      $ python manage.py createsuperuser

For convenience, you can keep your normal user logged in on Chrome and your superuser logged in on Firefox (or similar), so that you can see how the site behaves for both kinds of users.

### Type checks

Running type checks with mypy:

    $ mypy maiagent

### Test coverage

To run the tests, check your test coverage, and generate an HTML coverage report:

    $ coverage run -m pytest
    $ coverage html
    $ open htmlcov/index.html

#### Running tests with pytest

    $ pytest

### Live reloading and Sass CSS compilation

Moved to [Live reloading and SASS compilation](https://cookiecutter-django.readthedocs.io/en/latest/2-local-development/developing-locally.html#using-webpack-or-gulp).

### Celery

This app comes with Celery.

To run a celery worker:

```bash
cd maiagent
celery -A config.celery_app worker -l info
```

Please note: For Celery's import magic to work, it is important _where_ the celery commands are run. If you are in the same folder with _manage.py_, you should be right.

To run [periodic tasks](https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html), you'll need to start the celery beat scheduler service. You can start it as a standalone process:

```bash
cd maiagent
celery -A config.celery_app beat
```

or you can embed the beat service inside a worker with the `-B` option (not recommended for production use):

```bash
cd maiagent
celery -A config.celery_app worker -B -l info
```

## Deployment

The following details how to deploy this application.

### Docker

See detailed [cookiecutter-django Docker documentation](https://cookiecutter-django.readthedocs.io/en/latest/3-deployment/deployment-with-docker.html).

### Custom Bootstrap Compilation

The generated CSS is set up with automatic Bootstrap recompilation with variables of your choice.
Bootstrap v5 is installed using npm and customised by tweaking your variables in `static/sass/custom_bootstrap_vars`.

You can find a list of available variables [in the bootstrap source](https://github.com/twbs/bootstrap/blob/v5.1.3/scss/_variables.scss), or get explanations on them in the [Bootstrap docs](https://getbootstrap.com/docs/5.1/customize/sass/).

Bootstrap's javascript as well as its dependencies are concatenated into a single file: `static/js/vendors.js`.
