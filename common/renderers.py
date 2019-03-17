import bootstrap4.renderers


class FieldRenderer(bootstrap4.renderers.FieldRenderer):
    # todo remove when https://github.com/zostera/django-bootstrap4/issues/40
    # is fixed
    def fix_clearable_file_input(self, html):
        return html.replace('class="', 'class="w-100 form-control ')
