"""Main entry point
"""
from pyramid.config import Configurator
from exception_handler import ExceptionHandler

def main(global_config, **settings):
    config = Configurator(settings=settings)
    config.include("cornice")
    config.scan("cluster_rest.views")
    app = config.make_wsgi_app()
    app = ExceptionHandler(app)
    return app

