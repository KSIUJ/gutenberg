# Printer management
This document is intended for Gutenberg instance admins;
it explains how to configure printers and manage printing permissions.

> [!NOTE]
> This document is currently incomplete

## Admin interface
Management actions are performed in the Django admin interface,
which can be accessed by appending `/admin/` to the instance URL.

The simplest way to access it is to create a superuser account:
```bash
uv run manage.py createsuperuser
```

## Printer list
A new printer can be created in the **Control** > **Printers** section of the admin interface.

## Adding a printer via CUPS
[CUPS](https://openprinting.github.io/cups/) is the standard printing system on Linux operating systems.
CUPS provides a web interface for managing printers, which can be accessed at `http://localhost:631/`
on the server where the Gutenberg Celery worker is running.

When adding a printer a CUPS, the **Printer type** field should be set to **local cups**. 

You can use the web interface or the command below to find the list of available printers:
```bash
lpstat -v
```
Use the name (not the URL) from the output of the command above as the value of the **Cups printer name** field.

Most other fields are optional.

## Managing printing permissions
Only users who are in a group listed in the **Printer permissions** list can access the printer.
> [!NOTE]
> This restriction also applies to superuser accounts.
