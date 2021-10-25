"""
Templating using Jinja2.

For example::
    import jinja2
    import time

    template = Template(path='templates/')

    template_substvars = {
        'timestamp': timestamp,
        'now': time.time(),
    }

    template.render_to_file(template_name='template.j2',
                            template_vars=template_substvars,
                            output=output_filename)
"""

import datetime

import jinja2


class Template(object):

    def __init__(self, path):
        template_loader = jinja2.FileSystemLoader(searchpath=path)
        self.environment = jinja2.Environment(loader=template_loader)

    def render(self, template_name, template_vars=None):
        """
        Render a template, and return it.

        @param: template_name: The name of the template to render
        @param: template_vars A dictionary of variables to process

        @return: generated output
        """
        if template_vars is None:
            template_vars = {}
        temp = self.environment.get_template(template_name)
        return temp.render(template_vars)

    def render_to_file(self, template_name, output, template_vars=None):
        """
        Render a template, and write it to a file.

        @param template_name: The name of the template to render
        @param output:        The output filename
        @param template_vars: A dictionary of variables to process
        """
        content = self.render(template_name, template_vars)
        with open(output, 'w') as f:
            f.write(content.encode("utf-8"))


def timestamp(epochtime, time_format="%Y-%m-%d %H:%M:%S"):
    return datetime.datetime.fromtimestamp(epochtime).strftime(time_format)
