# Overview of Gutenberg's REST and IPP APIs.
## Existing API
The existing API endpoints map to corresponding IPP operations.
This design allows for the creation of a common backend.

### List of REST API endpoints and IPP operations

| API endpoint                          | IPP operation                                                                                                           | Notes                                                                                                                                                                                                                                                                                            |
|---------------------------------------|-------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `GET /api/printers/`                  | _not applicable_                                                                                                        | In Gutenberg IPP itself is not used for printer discovery. An `ipp:` (or `ipps:`) URI is specific to one printer. More recent updates to IPP add support for the `output-device` attribute, but it's not used in Gutenberg.                                                                      |
| `GET /api/printers/:printer_id/`      | [`Get-Printer-Attributes`](https://datatracker.ietf.org/doc/html/rfc8011#section-4.2.5) (RFC 8011)                      |                                                                                                                                                                                                                                                                                                  |
| `POST /api/jobs/submit/`              | [`Print-Job`](https://datatracker.ietf.org/doc/html/rfc8011#section-4.2.1) (RFC 8011)                                   |                                                                                                                                                                                                                                                                                                  |
| _none_                                | [`Validate-Job`](https://datatracker.ietf.org/doc/html/rfc8011#section-4.2.3) (RFC 8011)                                |                                                                                                                                                                                                                                                                                                  |
| `GET /api/jobs/`                      | [`Get-Jobs`](https://datatracker.ietf.org/doc/html/rfc8011#section-4.2.6) (RFC 8011)                                    |                                                                                                                                                                                                                                                                                                  |
| `GET /api/job/:id/`                   | [`Get-Job-Attributes`](https://datatracker.ietf.org/doc/html/rfc8011#section-4.3.4) (RFC 8011)                          |                                                                                                                                                                                                                                                                                                  |
| `POST /api/jobs/:id/cancel/`          | [`Cancel-Job`](https://datatracker.ietf.org/doc/html/rfc8011#section-4.3.3) (RFC 8011)                                  |                                                                                                                                                                                                                                                                                                  |
| `POST /api/jobs/create_job/`          | [`Create-Job`](https://datatracker.ietf.org/doc/html/rfc8011#section-4.2.4) (RFC 8011)                                  |                                                                                                                                                                                                                                                                                                  |
| `POST /api/jobs/:id/upload_artefact/` | [`Send-Document`](https://datatracker.ietf.org/doc/html/rfc8011#section-4.3.1) (RFC 8011)                               |                                                                                                                                                                                                                                                                                                  |
| `POST /api/jobs/:id/run_job/`         | [`Close-Job`](https://ftp.pwg.org/pub/pwg/candidates/cs-ippjobext21-20230210-5100.7.pdf) (PWG 5100.7-2023)              | This endpoint also maps to the [`Send-Document`](https://datatracker.ietf.org/doc/html/rfc8011#section-4.3.1) operation, but with `last-document` set to `true` and no file provided. This was the standard way of finishing a job in IPP v1.1 when the document count was not known in advance. |
| _none_                                | [`Identify-Printer`](https://ftp.pwg.org/pub/pwg/candidates/cs-ippjobprinterext3v10-20120727-5100.13.pdf) (PWG 5100.13) | Implemented as a no-op.                                                                                                                                                                                                                                                                          |

### Printing single-document print jobs in a single request
When a print job consists of only a single document, both the REST API and IPP provide a simple way to select print job
attributes and upload the file in a single request.
In IPP the [`Print-Job`](https://datatracker.ietf.org/doc/html/rfc8011#section-4.2.1) operation is used for this,
the REST API endpoint is `POST /api/jobs/submit/`.
The print job is started immediately after the upload is complete.

### Printing multi-document print jobs
1. A new, empty print job is created using the
    [`Create-Job`](https://datatracker.ietf.org/doc/html/rfc8011#section-4.2.4) IPP operation
    or the `POST /api/jobs/create_job/` endpoint.
    The print job attributes are supplied in this request, and they are used to print all the files.
    The server's response includes the job id, which is used for subsequent requests. 
2. Documents are uploaded sequentially using the
    [`Send-Document`](https://datatracker.ietf.org/doc/html/rfc8011#section-4.3.1) operation
    or the `POST /api/jobs/:id/upload_artefact/` endpoint.
3. To complete the print job and to enqueue it, the client must do one of the following:
    - Set the `last-document` (IPP) or `last` (REST API) flag in the last artifact upload request in the previous step. 
    - IPP only: execute an additional [`Send-Document`](https://datatracker.ietf.org/doc/html/rfc8011#section-4.3.1)
      operation with `last-document` set to `true` and no document data in the request body.
    - Execute the [`Close-Job`](https://ftp.pwg.org/pub/pwg/candidates/cs-ippjobext21-20230210-5100.7.pdf) operation
      or make a request to the `POST /api/jobs/:id/run_job/` endpoint.


## Planed extensions
### Job modifications
### Printing previews
### Per-document print attribute overrides
