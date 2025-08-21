# Gutenberg 3.2

Office printer gateway: print documents via web GUI or driverless IPP.

Made by [KSI UJ](http://ksi.ii.uj.edu.pl). Powered by Django, Celery and VueJS.

## Features

- Upload a file and print via webapp (installable as a PWA)
- Submit print requests via driverless IPP, compatible with Windows (generic postscript), Linux (cups ipp everywhere),
  Android (ipp everywhere), macOSX (cups ipp everywhere) and IOS (separate bonjour server required for AirPrint
  compatibility).
- Use any supported CUPS printer
- Support for printing PDFs, images (JPEG, PNG), documents (DOC, DOCX, ODT, RTF)
- Customize printing: enable color, enable duplex, number of copies
- Authentication via OIDC
- Per printer permissions

## Setup

- Printer: make printing available for server network
- Linux server: install drivers, configure CUPS
- Linux server: test `lp` command
- Check if you have following commands available: `convert` (`imagemagick`),
  `unoconv`, `gs` (`ghostscript`), `pdftk`, and `bbwrap` (`bubblewrap`)
    - Debian/Ubuntu: `sudo apt install imagemagick unoconv ghostscript bubblewrap pdftk`
    - Arch Linux: `sudo pacman -S imagemagick unoconv ghostscript bubblewrap pdftk`
- Gutenberg uses `uv` as the Python project manager.
  See https://docs.astral.sh/uv/getting-started/installation/ for install instructions.
- You will also need to have `yarn` or `npm` to build the web interface.

### Setting up the app (for the lazy people)

First, set the temporary `GUTENBERG_ENV` environment variable to one of these two values:

```sh
export GUTENBERG_ENV=local # local development
export GUTENBERG_ENV=production # production settings
```

And, if you haven't done it yet, set your `$EDITOR` variable:

```sh
export EDITOR=vim # flamewar starting in 3, 2, 1...
```

Now, execute the following commands:

```sh
export DJANGO_SETTINGS_MODULE=gutenberg.settings.${GUTENBERG_ENV}_settings
git clone https://github.com/KSIUJ/gutenberg.git
cd guttenberg

# Setup the Python virtual environment in .venv and install required packages.
# uv will also download the correct Python version based on pyproject.toml,
# if the version installed on your machine is different.
cd backend
uv sync
cd ../

cd backend/gutenberg/settings
cp ${GUTENBERG_ENV}_settings.py.example ${GUTENBERG_ENV}_settings.py
$EDITOR ${GUTENBERG_ENV}_settings.py # edit the values appropriately
cd ../../../

cd webapp
yarn install
yarn build
cd ../

# Execute all Python commands through uv
cd backend
uv run manage.py migrate
uv run manage.py runserver 0.0.0.0:11111
cd ../

# visit localhost:11111 and check if everything works
```

You will also need to start at least one worker. In the main directory after activating the virtual environment:

```sh
cd backend
uv run celery -A gutenberg worker -B -l INFO
```

For proper deployment (instead of `uv run manage.py runserver`), see the
[uWSGI documentation](http://uwsgi-docs.readthedocs.io/en/latest/tutorials/Django_and_nginx.html).

**IPP features might not work with `runserver`- proper front webserver is required** (works with eg. `nginx` + `uwsgi`).
This is due to an error in Django (or one of its dependencies) - the `Expect: 100-continue` HTTP header is not handled
properly by the development server (IPP standard requires it).

Please remember to add both `uwsgi` (or your server of choice) AND `celery` worker (including celery beat) to `systemd`
(or the init server you use).

Exemplary production configs for `systemd`, `uwsgi` and `nginx` setup are available in the `/examples/` directory.
## Configuration

Go to `<YOUR SERVER URL>/admin/`.
