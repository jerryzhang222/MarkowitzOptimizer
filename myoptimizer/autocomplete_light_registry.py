import autocomplete_light.shortcuts as al
import autocomplete_light
from models import Optimization, Stock

class OptimizationAutocomplete(autocomplete_light.AutocompleteModelBase):
    search_fields = ['^ticker']
    attrs={
        # This will set the input placeholder attribute:
        'placeholder': 'e.g. AAPL',
        # This will set the yourlabs.Autocomplete.minimumCharacters
        # options, the naming conversion is handled by jQuery
        'data-autocomplete-minimum-characters': 2,
    }
    widget_attrs={
        'data-widget-maximum-values': 4,
        # Enable modern-style widget !
        'class': 'modern-style',
    }
    model = Stock
    
#class OptimizationAutocomplete(autocomplete_light.AutocompleteListBase):
#   choices = ('AAPL','SBUX')
autocomplete_light.register(OptimizationAutocomplete)