# IPP and REST API overview
Gutenberg provides two APIs for interacting with it:
- a [REST API](./rest.md),
- an [Internet Printing Protocol (IPP) implementation](./ipp.md).

See their documentation pages for more details.

The REST API is intended for use in the webapp (UI) component of Gutenberg.
In the future a token-based authentication scheme might be implemented for use by other API clients.

Most existing REST API endpoints map to corresponding IPP operations and have similar semantics.
This design reduces the code duplication in the IPP and REST API modules.
The page [IPP and REST API comparison](./ipp-rest-comparision.md) contains a table which lists the matching REST API
endpoints and IPP operations.

## Standard sequences of operations for printing documents

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
