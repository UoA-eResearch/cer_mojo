# Enable virtualenv where cornice, pyramid and all the other python dependencies are installed
import site
site.addsitedir('/var/www/wsgi/env/lib/python2.6/site-packages')

from pyramid.paster import get_app
application = get_app('/var/www/wsgi/apps/cluster_rest/cluster_rest.ini', 'pyramidapp')
