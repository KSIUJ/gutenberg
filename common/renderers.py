import bootstrap4.renderers

from bootstrap4.utils import render_template_file, add_css_class


class FieldRenderer(bootstrap4.renderers.FieldRenderer):
    # todo remove these two methods when
    # https://github.com/zostera/django-bootstrap4/issues/29 is fixed
    def add_class_attrs(self, widget=None):
        super(FieldRenderer, self).add_class_attrs(widget=widget)

        classes = widget.attrs['class']

        if self.field.errors:
            if self.error_css_class:
                classes = add_css_class(classes, self.error_css_class)
        else:
            if self.field.form.is_bound:
                classes = add_css_class(classes, self.success_css_class)

        widget.attrs['class'] = classes

    def append_to_field(self, html):
        field_help = self.field_help or None
        field_errors = self.field_errors
        if field_help or field_errors:
            help_html = render_template_file(
                'bootstrap4/field_help_text_and_errors.html',
                context={
                    'field': self.field,
                    'field_help': field_help,
                    'field_errors': field_errors,
                    'layout': self.layout,
                    'show_help': self.show_help,
                }
            )
            html += help_html
        return html

    # todo remove when https://github.com/zostera/django-bootstrap4/issues/40
    # is fixed
    def fix_clearable_file_input(self, html):
        return html.replace('class="', 'class="w-100 form-control ')
