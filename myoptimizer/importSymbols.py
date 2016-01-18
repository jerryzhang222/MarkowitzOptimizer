import os, sys, django
sys.path.append('/home/jerryzhang/myoptimize')
os.environ['PYTHONPATH']= '/home/jerryzhang/myoptimize/'
os.environ['DJANGO_SETTINGS_MODULE'] = 'myoptimize.settings'
django.setup()
from myoptimizer.models import Stock, Optimization
import csv
import myoptimizer.models as models

def load_stocks(file_path):
    reader = csv.DictReader(open(file_path))
    for row in reader:
        stock = Stock(ticker=row['ticker'],name=row['name'])
        stock.save()

#Stock.objects.all().delete()
load_stocks("symbols.csv")