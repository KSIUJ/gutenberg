# Document processing

## Relevant IPP Job attributes affecting processing

Borderless printing:
- [`media-overprint`]
- [`media-overprint-distance`]
- [`media-overprint-method`]

Input pages to Scaled Pages:
- [`multiple-document-handling`]
- [`print-scaling`]
- [`orientation-requested`]

Scaled Pages to Final pages:
- [`page-ranges`]
- [`number-up`]

Impressions:
- [`imposition-template`]

Postprocessing:
- [`copies`]
- [`sides`]

Other:
- [`image-orientation`]
- [`page-delivery`]

## Determining input page size and final layout
Final page orientation is the same as [`orientation-requested`] if [`number-up`] is 1, 4, 16, etc.
and is rotated by 90 degrees clockwise if [`number-up`] is 2, 8 etc.

[`media-overprint`]: https://ftp.pwg.org/pub/pwg/candidates/cs-ippnodriver20-20230301-5100.13.pdf
[`media-overprint-distance`]: https://ftp.pwg.org/pub/pwg/candidates/cs-ippnodriver20-20230301-5100.13.pdf
[`media-overprint-method`]: https://ftp.pwg.org/pub/pwg/candidates/cs-ippnodriver20-20230301-5100.13.pdf
[`page-delivery`]: https://ftp.pwg.org/pub/pwg/candidates/cs-ippppx20-20230131-5100.3.pdf
[`multiple-document-handling`]: https://datatracker.ietf.org/doc/html/rfc8011#section-5.2.4
[`print-scaling`]: https://ftp.pwg.org/pub/pwg/candidates/cs-ippnodriver20-20230301-5100.13.pdf
[`orientation-requested`]: https://datatracker.ietf.org/doc/html/rfc8011#section-5.2.10
[`page-ranges`]: https://datatracker.ietf.org/doc/html/rfc8011#section-5.2.7
[`number-up`]: https://datatracker.ietf.org/doc/html/rfc8011#section-5.2.9
[`imposition-template`]: https://ftp.pwg.org/pub/pwg/candidates/cs-ippppx20-20230131-5100.3.pdf
[`copies`]: https://datatracker.ietf.org/doc/html/rfc8011#section-5.2.5
[`sides`]: https://datatracker.ietf.org/doc/html/rfc8011#section-5.2.8
[`image-orientation`]: https://ftp.pwg.org/pub/pwg/candidates/cs-ippppx20-20230131-5100.3.pdf  
