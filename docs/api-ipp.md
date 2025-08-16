# Overview of Gutenberg's REST and IPP APIs.
## Existing API
The existing API endpoints map to corresponding IPP operations.
This design allows for the creation of a common backend.

### List of REST API endpoints and IPP operations

| API endpoint                          | IPP operation                                                                                                           | Notes                                                                                                                                                                                                                                                                                                  |
|---------------------------------------|-------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `GET /api/printers/`                  | _not applicable_                                                                                                        | In Gutenberg IPP itself is not used for printer discovery. An `ipp:` (or `ipps:`) URI is specific to one printer. More recent updates to IPP add support for the `output-device` attribute, but it's not used in Gutenberg.                                                                            |
| `GET /api/printers/:printer_id/`      | [`Get-Printer-Attributes`](https://datatracker.ietf.org/doc/html/rfc8011#section-4.2.5) (RFC 8011)                      |                                                                                                                                                                                                                                                                                                        |
| `POST /api/jobs/submit/`              | [`Print-Job`](https://datatracker.ietf.org/doc/html/rfc8011#section-4.2.1) (RFC 8011)                                   |                                                                                                                                                                                                                                                                                                        |
| _none_                                | [`Validate-Job`](https://datatracker.ietf.org/doc/html/rfc8011#section-4.2.3) (RFC 8011)                                |                                                                                                                                                                                                                                                                                                        |
| `GET /api/jobs/`                      | [`Get-Jobs`](https://datatracker.ietf.org/doc/html/rfc8011#section-4.2.6) (RFC 8011)                                    |                                                                                                                                                                                                                                                                                                        |
| `GET /api/job/:id/`                   | [`Get-Job-Attributes`](https://datatracker.ietf.org/doc/html/rfc8011#section-4.3.4) (RFC 8011)                          |                                                                                                                                                                                                                                                                                                        |
| `POST /api/jobs/:id/cancel/`          | [`Cancel-Job`](https://datatracker.ietf.org/doc/html/rfc8011#section-4.3.3) (RFC 8011)                                  |                                                                                                                                                                                                                                                                                                        |
| `POST /api/jobs/create_job/`          | [`Create-Job`](https://datatracker.ietf.org/doc/html/rfc8011#section-4.2.4) (RFC 8011)                                  |                                                                                                                                                                                                                                                                                                        |
| `POST /api/jobs/:id/upload_artefact/` | [`Send-Document`](https://datatracker.ietf.org/doc/html/rfc8011#section-4.3.1) (RFC 8011)                               |                                                                                                                                                                                                                                                                                                        |
| `POST /api/jobs/:id/run_job/`         | [`Close-Job`](https://ftp.pwg.org/pub/pwg/candidates/cs-ippjobext21-20230210-5100.7.pdf) (PWG 5100.7-2023)              | This endpoint also maps to the [`Send-Document`](https://datatracker.ietf.org/doc/html/rfc8011#section-4.3.1) operation, but with `last-document` set to `true` and no file provided. This used to be the standard way of finishing a job in IPP v1.1 when the document count is not known in advance. |
| _none_                                | [`Identify-Printer`](https://ftp.pwg.org/pub/pwg/candidates/cs-ippjobprinterext3v10-20120727-5100.13.pdf) (PWG 5100.13) | Implemented as a no-op.                                                                                                                                                                                                                                                                                |

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
The first two extensions are designed with the [#63 Printing Previews](https://github.com/KSIUJ/gutenberg/issues/63)
feature in mind. The previews will be generated on the server (likely in a Celery worker), not on the client device.
This requires uploading documents before the request to start the print job is made.
As the user might want to modify the print settings after generating a preview, new endpoints and operations for
modifying a print job are needed. Without them, the client would have to create new jobs for each preview, which
would require reuploading the documents each time.

### Job modifications
The goal of this extension is to allow the client to perform the following actions on a job:
1. Modify job attributes
2. Get the file list
3. Delete an uploaded file
4. Change the document print order

The first two actions can be implemented using standard IPP operations.
#### Modify job attributes
RFC 3380 defines the [`Set-Job-Attributes`](https://datatracker.ietf.org/doc/html/rfc3380#section-4.2) IPP operation,
which does exactly what we need for this action.

The REST API endpoint for this action could be `PATCH /api/jobs/:id/`. Alternatively a `POST` action could be added.
While a `PATCH` request is not required to be idempotent, our implementation of this endpoint probably should be.
See the [MDN docs for the `PATCH` request method](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods/PATCH).

The IPP operation must be atomic, which means it must either change all requested attributes or none.
The REST API endpoint should also be atomic.

The IPP operation is also sparse, meaning the client only has to provide the attributes which it wishes to change.
This REST API endpoint should also allow sparse updates so that the addition of a new attribute is not a breaking change.

##### Unsupported job configuration handling
...

#### ...
#### ...
#### ...

### Printing previews
...

### Per-document print attribute overrides
...
