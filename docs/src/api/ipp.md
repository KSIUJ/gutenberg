# Internet Printing Protocol (IPP)
The Internet Printing Protocol is an extensible protocol maintained by the [Printer Working Group](https://www.pwg.org/).
Check the [IPP Guide](https://www.pwg.org/ipp/ippguide.html) for an overview of IPP.

Gutenberg implements an IPP server. The IPP operations are not proxied directly to the physical printer but are handled
by Gutenberg. Gutenberg verifies printing permissions, manages accounting (print stats and quotas) and processes the
supplied documents. This has the implications of: 
1. Gutenberg might support some IPP operations, attributes or formats that the physical printer does not.
    (E.g., it might support submitting .docx files, even if the physical printer can only accept PDFs. In this case
    Gutenberg will convert the document to PDF, which it will then send to the printer).
2. Some operations, attributes or formats supported by the physical printer might not be supported when printing via
    Gutenberg. (E.g., the printer might support stapling the media sheets after a print job is complete, but there is no
    way to use this feature via Gutenberg).

## Supported IPP standards and versions
...

## Supported IPP operations
...

## Supported job attributes
...

## Supported file formats
...

## Authentication
...
