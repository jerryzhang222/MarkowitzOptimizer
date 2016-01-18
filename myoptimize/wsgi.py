"""
WSGI config for myoptimize project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/howto/deployment/wsgi/
"""

import os, sys, django

from django.core.wsgi import get_wsgi_application
sys.path.append('/home/jerryzhang/myoptimize')
os.environ['PYTHONPATH']= '/home/jerryzhang/myoptimize/'
os.environ['DJANGO_SETTINGS_MODULE'] = 'myoptimize.settings'
django.setup()
from whitenoise.django import DjangoWhiteNoise

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myoptimize.settings")

application = get_wsgi_application()

from django.core.wsgi import get_wsgi_application
from dj_static import Cling

application = Cling(get_wsgi_application())
application = DjangoWhiteNoise(application)