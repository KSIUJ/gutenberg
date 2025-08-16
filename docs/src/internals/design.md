# UX and implementation suggestions for Gutenberg
## Goals
### Printing and config
- Simple printing should be as easy as possible. 
File upload should be possible from the main page.
- There should be an indication of what file types are allowed.
### Print config
- The printing logic should be ready for manual duplex printing,
  which involves a two-stage printing process.
- The UI should support settings specific for a given format.
- If printing multiple files at once is possible, it should be possible
  to edit some settings separately for each file.
- The UI should not be overwhelming, irrelevant settings should be hidden.
- If possible, settings should include a visual explanation.
  If the preview option is good enough, this might not be necessary.
### Preview
- The user should be able to tell exactly what the printed pages will look like. 
- It should be easy to tell the order of the resulting pages and the backsides of the pages.
  For duplex printing, the user should be able to clearly see the difference between the
  "Two-sided (long edge)" and "Two-sided (short edge)" options.
- The user should never see a not up-to-date preview.
### IPP
- The IPP feature should be easily discoverable from the main page.
- This feature should be easy to understand for non-technical users.
### Print queue
- If there are documents in the user's print queue, an indicator for that should be visible on all/most pages.
- It should be possible to cancel a print job from the print queue.
### General UI
- The page should be responsive.
- The UX on mobile and desktop can be different.
For example, some options that are always visible on desktop can on mobile
appear only after uploading the first file.
- A button with the text `Print` should only be used to start the print job.

## UI
### Main page
On desktop, the main page will use a two-column layout with a header:
The header contains the logo and a user menu.

The left column contains only a card with file upload elements and configuration options.
The card will be prominent.

The right column will describe other ways to print: IPP and the REST API.
It could also describe what Gutenberg is and how to use to self-host it.

### Print preview
After uploading files, the user should be presented with the buttons `Preview` and `Print`.
Clicking `Preview` takes the user to the preview mode:

On desktop the upload + config card will remain visible and will be moved to the left screen edge,
the right side will transform to show the print preview.

On mobile the preview will take the whole screen, there should be a button to close it and
go back to modify the print config. 

The preview updates automatically after the user changes the configuration.
While a new preview is loading, the previous preview is grayed out.

The preview can have multiple display modes:
#### 2D mode
This view shows all the pages in a reasonable order.
It should be decided if this order respects the "Reverse order" setting.
The user can change the preview orientation (independently of the print settings).

If duplex printing is enabled, the preview shows the backsides next to the front sides.
The front pages are always on the left, the back pages on the right.
The back page should bo oriented as if the page was flipped along the common, vertical edge
(in the selected preview orientation) between the front and back pages.
In particular this means that if the pages are displayed in landscape mode,
plus the "Two-sided (long edge)" option is selected, or portrait mode + "Two-sided (short edge)",
the right page is rotated 180 degrees.

The rationale for this is that if the user selects the display orientation that places
the front page upright, they will be able to see if the back page is upside down.

#### 3D mode
This view shows the pages in an isometric 3D view as if they were printed on paper and stacked.
The order should match the order in the stack of printed pages.
This requires admin configuration.
The backsides are revealed by a 3D rotation on hover.

## Suggested API design for the web app to support the printing preview feature
To print a document, the API client first asks the server to create a print job ID.
Each job ID has an associated expiration time.

The client can alter a print job (identified by its ID) by uploading and deleting files.
They can also get the list of uploaded files.

The client can also:
- Request a preview of the print job.
- Request to print the job.
- Cancel the print job.

The request for print and preview should take print settings,
including file-specific settings, in the request body.
They both start by preprocessing the input files into a ready-to-print PDF file.
After that:
- the preview request generates (low-quality) images for each page in the PDF,
  and any additional metadata needed to display the preview.
  Techniques like [CSS Sprites](https://css-tricks.com/css-sprites/) could be used 
  to load all images in a single request;
- the print request starts the print job by sending the PDF to the printer via CUSP.

As both the print and preview requests create the same PDF file, job-scoped caching could be used
to avoid generating the same PDF multiple times if the settings and input files have not changed.

Please note that the preprocessing job might take a while to complete, and it is done asynchronously
in a celery worker. The API design should account for this:
- when a new preview is requested, the previous request generation celery task should be canceled. 
- the behavior when a print is requested while the preview is being generated should be specified.
- there needs to be a way for the server to notify the client that the preview is ready.
  Long-running HTTP requests could be used for this, consider using server-side events 
  and separating the endpoints for a preview request and preview image retrieval.

After a print is requested, the settings could be stored.
It should probably not be allowed to request printing multiple times.
This note might not apply if the print failed.

Any action, especially starting the print job, should extend the expiration time of the job.
After the expiration time passes, the job is canceled and all of its associated files are deleted.

## Simpler API for programmatic use
There should probably also exist a basic API that allows uploading all files, setting the print config
and start printing in a single request.
The `multipart/form-data` format could be used here.
As the print settings might become complex over time, I suggest using a JSON part instead of separate
form fields for sending the settings.
