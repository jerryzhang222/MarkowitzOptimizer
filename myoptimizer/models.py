from django.db import models
from decimal import Decimal

class Stock(models.Model):
    ticker = models.CharField(max_length=20)
    name = models.CharField(max_length=200, blank = True)
    
    def __str__(self):              # __unicode__ on Python 2
        return self.ticker
        
class Optimization(models.Model):
    cash = models.FloatField(default=Decimal('10000.00'),blank = True, null=True)
    security = models.ForeignKey(Stock, on_delete=models.CASCADE)

# Create your models here.
