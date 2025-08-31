# Gutenberg 3.2

Office printer gateway: print documents via web GUI or driverless IPP.

Made by [KSI UJ](http://ksi.ii.uj.edu.pl). Powered by Django, Celery and VueJS.

## Features

- Upload a file and print via webapp
- Submit print requests via driverless IPP, compatible with Windows (generic postscript), Linux (cups ipp everywhere),
  Android (ipp everywhere), macOSX (cups ipp everywhere) and IOS (separate bonjour server required for AirPrint
  compatibility).
- Use any supported CUPS printer
- Support for printing PDFs, images (JPEG, PNG), documents (DOC, DOCX, ODT, RTF)
- Customize printing: enable color, enable duplex, number of copies
- Authentication via OIDC
- Per printer permissions

## Setup

See the documentation at <https://ksiuj.github.io/gutenberg/admin/setup.html>

## Configuration

Go to `<YOUR SERVER URL>/admin/`.
