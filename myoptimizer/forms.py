from django import forms
from decimal import Decimal
import autocomplete_light
from models import Optimization

class SecurityForm(forms.Form):
    cash = forms.DecimalField(initial=Decimal('10000.00'),max_value=1000000000000,min_value=100,required=False)
    security = forms.CharField(required=False)
   # securities = forms.CharField(widget=forms.Textarea,required=False)
   
class OptimizationModelForm(autocomplete_light.ModelForm):
    class Meta:
        autocomplete_names = {'security': 'OptimizationAutocomplete'}
        model = Optimization
        autocomplete_fields = ('security')
        fields = '__all__'
    def __init__(self, *args, **kwargs):
        super(OptimizationModelForm, self).__init__(*args, **kwargs)
        self.fields['cash'].widget = forms.widgets.TextInput(attrs={
            'class': 'modern-style autocomplete-light-widget',
            'name': 'Cash:'})
        self.fields['security'].required = False
        
#class OptimizationModelForm(forms.ModelForm):
#    class Meta:
#        model = Optimization
#        widgets = {
#            'security': autocomplete_light.TextWidget('OptimizationAutocomplete'),
#        }
#        fields = '__all__'