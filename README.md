# Gutenberg 3.0
Simple proxy for HP LaserJet 500 printer: print documents via web GUI - made
for internal use of [KSI UJ](http://ksi.ii.uj.edu.pl). 


## Features
  - Upload a file and print
  - Support for printing PDFs, images (JPEG, PNG), documents (DOC, DOCX, ODT,
    RTF) 
  - Customize print: enable duplex, number of copies
  - Authentication via CAS
  - sudo printing - color print (only for whitelisted people via CAS group)

## Setup
  - Printer: make printing available for server network
  - Linux server: install drivers, configure CUPS
  - Linux server: test `lp` command
  - Check if you have following commands available: `convert` (`imagemagick`),
    `unoconv`, `gs` (`ghostscript`), and `bbwrap` (`bubblewrap`) 
    - Debian/Ubuntu: `sudo apt install imagemagick unoconv ghostscript
      bubblewrap`
    - Arch Linux: `sudo pacman -S imagemagick unoconv ghostscript bubblewrap`

### Setting up the webapp (for the lazy people)
First, set the temporary `GUTENBERG_ENV` environment variable to one of these
two values: 
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
virtualenv -p python3 venv
source venv/bin/activate
git clone https://github.com/KSIUJ/gutenberg.git
cd gutenberg/gutenberg/settings
cp ${GUTENBERG_ENV}_settings.py.example ${GUTENBERG_ENV}_settings.py
$EDITOR ${GUTENBERG_ENV}_settings.py # edit the values appropriately
cd ../..
python manage.py runserver 0.0.0.0:11111
# visit localhost:11111 and check if everything works
```

For proper deployment (instead of `manage.py runserver`), see the
[uWSGI documentation](http://uwsgi-docs.readthedocs.io/en/latest/tutorials/Django_and_nginx.html).  
