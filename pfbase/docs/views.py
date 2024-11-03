from django.views.generic import TemplateView


class DocsView(TemplateView):
    template_name = 'swagger.html'
