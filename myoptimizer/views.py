from django.shortcuts import render
from .forms import SecurityForm, OptimizationModelForm
from .markowitz import markowitz, perfectPortfolio
from django.contrib.staticfiles.templatetags.staticfiles import static
from html import HTML
import urllib2, csv
import os, sys, django
sys.path.append('/home/jerryzhang/myoptimize')
os.environ['PYTHONPATH']= '/home/jerryzhang/myoptimize/'
os.environ['DJANGO_SETTINGS_MODULE'] = 'myoptimize.settings'
django.setup()
from myoptimizer.models import Stock
import json

def home(request):
    form = OptimizationModelForm(request.POST or None)
    context = {"form":form, "portfolio_table":"You haven't added any securities yet."}
    
    if 'portfolio_table' in request.session:
        context = {"form":form, "portfolio_table":request.session['portfolio_table']}
        
    if request.POST:
        remove_keys = [key for key in request.POST if key.startswith("_remove")]
        if '_add' in request.POST:
            if form.is_valid():
                print form.cleaned_data
                if 'current_ticker_list' in request.session and type(request.session['current_ticker_list']) == list:
                    current_ticker_list = request.session['current_ticker_list']
                    current_ticker_list.append(form.cleaned_data['security'].ticker)
                    request.session['current_ticker_list'] = current_ticker_list
                else:
                    request.session['current_ticker_list'] = [form.cleaned_data['security'].ticker]
                request.session['portfolio_table'] = makeTable(['Company Name','Price','52-Week Range'], request.session['current_ticker_list'])
                form = OptimizationModelForm()
                context = {"form":form, "current_ticker_list":request.session['current_ticker_list'], "portfolio_table": request.session['portfolio_table']}
        elif '_optimize' in request.POST:
            if form.is_valid():
                new_portfolio = portSecurities()
                securities = request.session['current_ticker_list']
                cash = float(form.cleaned_data['cash'])
                context = getHome(request, securities, cash, form, new_portfolio)
        elif len(remove_keys) > 0:
            current_ticker_list = request.session['current_ticker_list']
            current_ticker_list.remove(str(remove_keys[1])[8:-2])
            request.session['current_ticker_list'] = current_ticker_list
            request.session['portfolio_table'] = makeTable(['Company Name','Price','52-Week Range'], request.session['current_ticker_list'])
            context = {"form":form, "current_ticker_list":request.session['current_ticker_list'], "portfolio_table": request.session['portfolio_table']}
        elif '_clear' in request.POST:
            request.session['current_ticker_list'] = None
            request.session['portfolio_table'] = "You haven't added any securities yet."
            context = {"form":form, "current_ticker_list":request.session['current_ticker_list'], "portfolio_table":request.session['portfolio_table']}
                
    template = "home.html"
    return render(request, template, context)
    
def getHome(request, securities, cash, form, new_portfolio):
    returns_plot, price_plot, frontier_plot = None, None, None
    recommended_port = None
    equalweight_returns, optimal_returns = None, None
    
    new_portfolio.ticker_list = securities
    new_portfolio.optimalPortfolio(cash)
    new_portfolio.doMarkowitz(cash)
    returns_plot = new_portfolio.returns_plot
    price_plot = new_portfolio.price_plot
    equalweight_returns = new_portfolio.equalweight_returns
    optimal_returns = new_portfolio.optimal_returns
    frontier_plot = new_portfolio.frontier_plot
    request.session['frontier_plot']=frontier_plot
    recommended_port = new_portfolio.shareWeights
    percentWeights = new_portfolio.percentWeights
    
    request.session['portfolio_table'] = makeTable(['Company Name','Price','52-Week Range'], request.session['current_ticker_list'], recommended_port, percentWeights)
    
    homeContext = {"form": form, "returns_plot": returns_plot, "price_plot": price_plot, 
                "frontier_plot": frontier_plot, "equalweight_returns": equalweight_returns,
                "optimal_returns": optimal_returns, "recommended_port": recommended_port,
                "current_ticker_list":request.session['current_ticker_list'], "portfolio_table": request.session['portfolio_table']}
    
    return homeContext

def frontierPlot(request):
    return request.session['frontier_plot']

def makeTable(header, current_ticker_list, recommended_port = None, percentWeights = None):
    if recommended_port != None:
        t = '<table class="rwd-table" width="100%"><tr><th>Ticker</th><th>Company Name</th><th>Price</th><th>52-Week Range</th><th>% Weights</th><th>Shares to Buy</th></tr>'
    else:
        t = '<table class="rwd-table" width="100%"><tr><th>Ticker</th><th>Company Name</th><th>Price</th><th>52-Week Range</th></tr>'

    for ticker in current_ticker_list:
        req = urllib2.Request('http://download.finance.yahoo.com/d/quotes.csv?s=' + ticker + '&f=npw&e=.csv')
        response = urllib2.urlopen(req)
        the_page = csv.reader(response)
        
        ticker_info = list(the_page)
        ticker_info = [item for sublist in ticker_info for item in sublist]
        
        t = t + '<tr><td data-th="Ticker">' + ticker + '</td>'
        t = t + '<td data-th="Company Name">' + ticker_info[0] + '</td>'
        t = t + '<td data-th="Price">' + ticker_info[1] + '</td>'
        t = t + '<td data-th="52-Week Range">' + ticker_info[2] + '</td>'
        
        if recommended_port != None:
            t = t + '<td data-th="% Weights">' + str('{0:.2f}%'.format(float(percentWeights[ticker] * 100))) + '</td>'
            t = t + '<td data-th="Shares to Buy">' + str(recommended_port[ticker]) + '</td><td><input type ="image" name="_remove_' + ticker + '"src="static/img/removeglyph.png" alt="Remove" width="18px" height="18px"></td></tr>'
        else:
            t = t + '<td><input type ="image" name="_remove_' + ticker + '"src="static/img/removeglyph.png" alt="Remove" width="18px" height="18px"></td></tr>'
        
    t = t + '</table>'
    return t
    
def get_stocks(request):
    if request.is_ajax():
        q = request.GET.get('term', '')
        stocks = Stock.objects.filter(ticker__startswith = q )[:20]
        results = []
        for stock in stocks:
            stock_json = {}
            stock_json = stock.ticker
            results.append(stock_json)
        data = json.dumps(results)
    else:
        data = 'fail'
    mimetype = 'application/json'
    print data
    return HttpResponse(data, mimetype)
    
class portSecurities:
    def __init__(self):
        self.ticker_list = []
    def doMarkowitz(self, cash):
        self.raw_data, self.returns_plot, self.price_plot, self.frontier_plot, self.equalweight_returns, self.optimal_returns = markowitz(self.ticker_list, cash)
    def optimalPortfolio(self, cash):
        self.percentWeights, self.shareWeights = perfectPortfolio(self.ticker_list, cash)
    def addSecurity(self, security):
        self.ticker_list.append(security)
        return self.ticker_list
        