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

> [!NOTE]
> The URLs for the endpoints below are not final, defaults generated by the
> [Django REST Framework's ViewSet](https://www.django-rest-framework.org/tutorial/6-viewsets-and-routers/) feature
> should be used where possible.

### Job modifications
The goal of this extension is to allow the client to perform the following actions on a job:
1. Modify job attributes
2. Get the document (file) list
3. Delete an uploaded document
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
The IPP operations
[`Print-Job`](https://datatracker.ietf.org/doc/html/rfc8011#section-4.2.1),
[`Validate-Job`](https://datatracker.ietf.org/doc/html/rfc8011#section-4.2.3),
[`Create-Job`](https://datatracker.ietf.org/doc/html/rfc8011#section-4.2.4) and
[`Set-Job-Attributes`](https://datatracker.ietf.org/doc/html/rfc3380#section-4.2)
should verify if the selected print configuration is valid and reject the operation if it is not (e.g., if some pair of 
provided attribute values is conflicting).

The same behavior might not be the optimal solution for the REST API.
When the user is modifying to the print configuration, it is desirable to store it on the server after each change in
the UI (with proper throttling/debouncing on the webapp side). This way refreshing the page will not cause data loss, 
as the web app can retrieve the stored configuration after the reload.

The suggested behavior in this case is to allow setting syntactically valid attributes that result in a configuration
not supported by the selected printer in requests to `POST /api/jobs/create_job/` and `PATCH /api/jobs/:id/`.
If the selected job configuration is invalid, the responses to these requests should indicate operation success (a 2xx
status code) but should include a `errors` field in the response body, indicating the errors in the selected
configuration. A human-readable warning message should be included for displaying in the webapp UI. The output could
also include the warnings in a structured form, just like it would be returned from the IPP operations.

The server should return a failure response for calls to `POST /api/jobs/submit/` and `POST /api/jobs/:id/run_job/`
if the current job configuration is invalid.
The same validation should also happen when executing IPP operations which
start the print job ([`Print-Job`](https://datatracker.ietf.org/doc/html/rfc8011#section-4.2.1),
[`Send-Document`](https://datatracker.ietf.org/doc/html/rfc8011#section-4.3.1) with `last-document` set to `true`
and [`Close-Job`](https://ftp.pwg.org/pub/pwg/candidates/cs-ippjobext21-20230210-5100.7.pdf)) and the
[`Validate-Job`](https://datatracker.ietf.org/doc/html/rfc8011#section-4.2.3) operation,
as the configuration might be invalid if it has been created via IPP but modified using the REST API.

The list of errors could also be retrievable using a new endpoint or could be included in the response to calls to the
`GET /api/job/:id/` endpoint.

#### Get the document list
The IPP operations suitable for this action are
[`Get-Documents`](https://ftp.pwg.org/pub/pwg/candidates/cs-ippdocobject12-20240517-5100.5.pdf)
and [`Get-Document-Attributes`](https://ftp.pwg.org/pub/pwg/candidates/cs-ippdocobject12-20240517-5100.5.pdf).

In the REST API the file list could be returned either in the response from `GET /api/job/:id/` or using a new
[`ViewSet`](https://www.django-rest-framework.org/tutorial/6-viewsets-and-routers/) endpoint supporting the requests to
`GET /api/job/:id/documents/` and `GET /api/job/:id/documents/:doc_id/`.
The `ViewSet` solution follows the convention of providing a 1 to 1 mapping of the REST API endpoints to IPP operations.

#### Delete document
A simple `DELETE /api/job/:id/documents/:doc_id/` endpoint could accomplish this action in the REST API.

There is no IPP operation suitable to accomplish this action:
- The [`Delete-Document`](https://ftp.pwg.org/pub/pwg/candidates/cs-ippdocobject10-20031031-5100.5.pdf) action defined in
    the [PWG 5100.5-2003 Standard for IPP Document Object](https://ftp.pwg.org/pub/pwg/candidates/cs-ippdocobject10-20031031-5100.5.pdf)
    standard has since been obsoleted and must not be implemented. Even if it wasn't, it could not be used for this purpose,
    as it can only be used by the printer's operators and administrators, not end-users.
- The [`Cancel-Document`](https://ftp.pwg.org/pub/pwg/candidates/cs-ippdocobject12-20240517-5100.5.pdf) operation has
    undesirable semantics. If the [`Resubmit-Job`](https://ftp.pwg.org/pub/pwg/candidates/cs-ippepx20-20240315-5100.11.pdf)
    operation or another way to rerun jobs is implemented, the previously canceled documents should get printed again.

As such, this endpoint should not be marked as mapping to `Delete-Document` or `Cancel-Document`.

#### Modify document order
For this action a `POST /api/job/:id/documents/reorder` endpoint could be provided accepting the new document print
order in the request body, for example:
```json
{
  "order": ["B", "A", "C"]
}
```
The server should verify that all documents are included exactly once.

There does not exist a standard IPP operation for this action.

### Printing previews
This feature is described in [PR #63](https://github.com/KSIUJ/gutenberg/issues/63). 
...

### Per-document print attribute overrides
This feature is described in [PR #94](https://github.com/KSIUJ/gutenberg/issues/94).

This could be an opportunity to implement the
[PWG 5100.5-2024 – IPP Document Object v1.2](https://ftp.pwg.org/pub/pwg/candidates/cs-ippdocobject12-20240517-5100.5.pdf)
standard.

#### Issues with the IPP operations for document management actions
The [`Get-Documents`](https://ftp.pwg.org/pub/pwg/candidates/cs-ippdocobject12-20240517-5100.5.pdf),
[`Get-Document-Attributes`](https://ftp.pwg.org/pub/pwg/candidates/cs-ippdocobject12-20240517-5100.5.pdf)
map directly to the `GET /api/job/:id/documents/` and `GET /api/job/:id/documents/:doc_id/` operations described in the
**Job modifications** section above.

This IPP standard uses sequential document numbers for identifying the documents.
The obsoleted [`Delete-Document`](https://ftp.pwg.org/pub/pwg/candidates/cs-ippdocobject10-20031031-5100.5.pdf)
operation creates a gap in the numbering.
This numbering also represents the order in which the documents will be processed. This presents an issue for the
**modify document order** action, as the document numbers used by IPP will need to be changed after modifying the
document order.

One possible solution to this issue would be to assign new numbers to all the documents if the order
gets changed. For example, assume there are three documents **A**, **B**, **C** initially in this order identified in
IPP by the numbers: **A:1**, **B:2**, **C:3**. When the REST API client changes the order to **C**, **B**, **A**, these
documents will be assigned the numbers **C:4**, **D:5**, **E:6**.
Since in this scenario the number of a document can change, the REST API should use different, persistent document IDs.

The [`Cancel-Document`](https://ftp.pwg.org/pub/pwg/candidates/cs-ippdocobject12-20240517-5100.5.pdf) operation required
by this standard is semantically different from the proposed document delete endpoint. A canceled document should remain
in the document list and will get printed if the job is resubmitted. The webapp should display this canceled status
in the job file list.
