# REST API
Gutenberg implements a REST API using [Django REST framework](https://www.django-rest-framework.org/).
The endpoint for the REST API is `<GUTENBERG_INSTANCE_URL>/api/`.

You can explore the API by browsing it. DRF generates interactive HTML views for all routes.

<div class="warning">

The auto-generated documentation is currently incomplete and in some cases displays incorrect schemas.

</div>

## Authentication
The REST API supports only cookie-based session authentication. This makes it unsuitable for uses other than the
Gutenberg's webapp. Support for other authentication schemes might be added in the future.
