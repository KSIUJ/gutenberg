# Document processing

## Document processing steps and relevant IPP Job attributes

1. Preprocess the documents:
    - Optionally convert to PDF with a page size taken from the document data
    - Determine the orientation of the document data
2. Determine the Input Page size based on the available Media Sheet size and the settings:
    - [`number-up`]``
    - [`orientation-requested`] or the orientation of the document data
    - [`imposition-template`]
    - optionally [`image-orientation`]
3. Place the preprocessed data on the Input Pages based on the determined Input Page size:
    - [`print-scaling`]
4. Filter pages and add required blank pages to the Input Pages:
    - [`page-ranges`]
    - [`sides`] and [`imposition-template`] determine the required blank page count
5. Place the Input Pages on the Final Pages:
    - [`number-up`]
    - as if using [`presentation-direction-number-up`] with the value of `toright-tobottom`
6. Place the Final Pages on the Media Sheet Pages (rotate if necessary):
    - [`imposition-template`]


## Other relevant IPP Job attributes:

Borderless printing:
- [`media-overprint`]
- [`media-overprint-distance`]
- [`media-overprint-method`]

Other:
- [`multiple-document-handling`]
- [`copies`]

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
[`presentation-direction-number-up`]: https://ftp.pwg.org/pub/pwg/candidates/cs-ippppx20-20230131-5100.3.pdf
