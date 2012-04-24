import sys
import traceback
import simplejson
from pyramid.httpexceptions import HTTPInternalServerError
from pyramid.response import Response

class ExceptionHandler(object):

  def __init__(self, application):
    self.app = application

  def __call__(self, environ, start_response):
    try:
      return self.app(environ, start_response)
    except:
      error_dict = {}
      error_dict['error'] = {}
      error_dict['error']['message'] = str(sys.exc_info()[1])
      error_dict['error']['stacktrace'] = traceback.format_exc()
      body = simplejson.dumps(error_dict)
      start_response('500 Internal Server Error',
        [ ('Content-Type', 'application/json'), ('Content-Length', str(len(body))) ] )
      return [ body ]

