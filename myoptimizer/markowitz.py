import sys
import zipline
from zipline.api import (add_history, 
                        history, 
                         set_slippage, 
                        slippage,
                        set_commission, 
                        commission, 
                        order_target_percent)

from zipline import TradingAlgorithm
from zipline.utils.factory import load_bars_from_yahoo
import pandas as pd
from pandas.io.data import DataReader
from datetime import datetime, timedelta
import numpy as np
import cvxopt as opt
from cvxopt import solvers
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt, mpld3
import warnings
import json
from PIL import Image
from django.http import HttpResponse

def optimal_portfolio(returns):
    n = len(returns)
    returns = np.asmatrix(returns)
    
    N = 100
    mus = [10**(5.0 * t/N - 1.0) for t in range(N)]
    
    # Convert to cvxopt matrices
    S = opt.matrix(np.cov(returns))
    pbar = opt.matrix(np.mean(returns, axis=1))
    
    # Create constraint matrices
    G = -opt.matrix(np.eye(n))   # negative n x n identity matrix
    h = opt.matrix(0.0, (n ,1))
    A = opt.matrix(1.0, (1, n))
    b = opt.matrix(1.0)
    
    # Calculate efficient frontier weights using quadratic programming
    portfolios = [solvers.qp(mu*S, -pbar, G, h, A, b)['x'] 
                  for mu in mus]
    ## CALCULATE RISKS AND RETURNS FOR FRONTIER
    returns = [np.dot(np.transpose(pbar), x) for x in portfolios]
    returns = np.concatenate(returns).ravel()
    risks = [np.sqrt(np.dot(np.transpose(x), S*x)) for x in portfolios]
    risks = np.concatenate(risks).ravel()
    sharpes = [this_return / this_risk for this_return,this_risk in zip(returns, risks)]
    final_portfolio = portfolios[sharpes.index(max(sharpes))]
    ## CALCULATE THE 2ND DEGREE POLYNOMIAL OF THE FRONTIER CURVE
    m1 = np.polyfit(np.asarray(returns), np.asarray(risks), 2)
    x1 = np.sqrt(m1[2] / m1[0])
    # CALCULATE THE OPTIMAL PORTFOLIO
    wt = solvers.qp(opt.matrix(x1 * S), -pbar, G, h, A, b)['x']
    #return np.asarray(wt), returns, risks
    return final_portfolio, returns, risks

def initialize(context):
    '''
    Called once at the very beginning of a backtest (and live trading). 
    Use this method to set up any bookkeeping variables.
    
    The context object is passed to all the other methods in your algorithm.

    Parameters

    context: An initialized and empty Python dictionary that has been 
             augmented so that properties can be accessed using dot 
             notation as well as the traditional bracket notation.
    
    Returns None
    '''
    # Register history container to keep a window of the last 100 prices.
    add_history(10, '1d', 'price')
    # Turn off the slippage model
    set_slippage(slippage.FixedSlippage(spread=0.0))
    # Set the commission model (Interactive Brokers Commission)
    set_commission(commission.PerShare(cost=0.0, min_trade_cost=0.0))
    context.tick = 0
    
def handle_data(context, data):
    '''
    Called when a market event occurs for any of the algorithm's 
    securities. 

    Parameters

    data: A dictionary keyed by security id containing the current 
          state of the securities in the algo's universe.

    context: The same context object from the initialize function.
             Stores the up to date portfolio as well as any state 
             variables defined.

    Returns None
    '''
    # Allow history to accumulate 100 days of prices before trading
    # and rebalance every day thereafter.
    context.tick += 1
    if context.tick < 10:
        return
    # Get rolling window of past prices and compute returns
    prices = history(10, '1d', 'price').dropna()
    returns = prices.pct_change().dropna()
    try:
        if context.tick == 9:
            _, opt_returns, opt_risks = optimal_portfolio(returns.T)
            plt.figure()
            frontier_plot = plt.plot(opt_risks, opt_returns, "y-o")
            plt.xlabel('std')
            plt.ylabel('mean')
            plt.savefig("plot.png")
            plt.clf()
        # Perform Markowitz-style portfolio optimization
        
        weights, _, _ = optimal_portfolio(returns.T)
        # Rebalance portfolio accordingly
        for stock, weight in zip(prices.columns, weights):
            order_target_percent(stock, weight)
    except ValueError as e:
        # Sometimes this error is thrown
        # ValueError: Rank(A) < p or Rank([P; A; G]) < n
        pass

def markowitz(stocks, cash):
    warnings.filterwarnings("once")
    
    solvers.options['show_progress'] = False

    end = pd.Timestamp.utcnow()
    start = end - 50 * pd.tseries.offsets.BDay()
    data = load_bars_from_yahoo(stocks=stocks,
                            start=start, end=end)

    # Instantinate algorithm        
    algo = TradingAlgorithm(initialize=initialize, 
                       handle_data=handle_data, cash=cash)
    # Run algorithm
    results = algo.run(data)
    
    # portfolio value plot
    raw_plot = results.portfolio_value.plot()
    raw_fig = raw_plot.get_figure()
    returns_plot = mpld3.fig_to_html(raw_fig)
    raw_fig.clf()
    
    #stock price plot
    raw_price_data = data.loc[:, :, 'price'].pct_change(1).fillna(0).applymap(lambda x: x + 1).cumprod().applymap(lambda x: x * 100)
    raw_price_plot = raw_price_data.plot(figsize=(8,5))
    raw_price_fig = raw_price_plot.get_figure()
    price_plot = mpld3.fig_to_html(raw_price_fig)
    raw_price_fig.clf()
    
    #final returns
    equalweight_returns = sum(map(list, raw_price_data.tail(1).values)[0]) / 4 - 100
    equalweight_returns = '{0:.2f}%'.format(float(equalweight_returns))
    optimal_returns = (results.portfolio_value.tail(1).iloc[0] - 100000) / 1000
    optimal_returns = '{0:.2f}%'.format(float(optimal_returns))
    
    #efficient frontier plot
    frontier_plot_data = open("plot.png", "rb").read()
    # serialize to HTTP response
    frontier_plot = HttpResponse(frontier_plot_data, content_type="image/png")
    
    return(results, returns_plot, price_plot, frontier_plot, equalweight_returns, optimal_returns)
    
def perfectPortfolio(stocks, cash):
    yahoo_pull = []
    solvers.options['show_progress'] = False
    
    for stock in stocks:
        yahoo_pull.append(DataReader(stock,  'yahoo', datetime.now() - timedelta(days=200), datetime.today())['Adj Close'])
    price_frame = pd.concat(yahoo_pull, axis = 1)
    price_frame.columns = stocks
    temp_price_frame = price_frame
    price_frame = price_frame.pct_change(1).transpose().fillna(0)
    final_weights = optimal_portfolio(price_frame)[0]
    while sum(1 for i in final_weights if i < 0.01) != 0:
        final_weights = adjustWeights(final_weights)
    percent_weights = formatToPercent(final_weights)
    shares = getShares(stocks,temp_price_frame.tail(1), cash, final_weights)
    return dict(zip(stocks, final_weights)), dict(zip(stocks,shares))

def adjustWeights(final_weights):
    num_trivial = sum(1 for i in final_weights if i < 0.01)
    sum_trivial = sum(i for i in final_weights if i < 0.01)
    num_non_trivial = len(final_weights) - num_trivial
    sum_non_trivial = sum(i for i in final_weights if i >= 0.01)
    
    arbitrary_divisor = 4.0
    percent_trivial = float(num_trivial) / len(final_weights)
    target_trivial = float(percent_trivial) / arbitrary_divisor
    target_non_trivial = 1 - target_trivial
    
    for index, stock in enumerate(final_weights):
        if stock >= 0.01:
            final_weights[index] = (stock / sum_non_trivial) * target_non_trivial
        else:
            final_weights[index] = (stock / sum_trivial) * target_trivial
    
    return final_weights

def formatToPercent(decimal_list):
    percent_list = []
    for index, decimal in enumerate(decimal_list):
        percent_list.append('{0:.2f}%'.format(float(decimal * 100)))
    return percent_list

def getShares(stocks, prices, cash, weights):
    temp = []
    for row in prices.iterrows():
        index, data = row
        temp.append(data.tolist())
    prices = temp[0]
    shares = []
    for index, stock in enumerate(stocks):
        shares.append(int(round(float(weights[index]) * cash / float(prices[index]))))
    return shares
        

#class portSecurities:
#    def __init__(self, tickers):
#        self.ticker_list = tickers
#    def doMarkowitz(self):
#        self.raw_data, self.returns_plot, self.price_plot, self.frontier_plot = markowitz(self.ticker_list)
        
#new_portfolio = portSecurities(['YUM', 'KO','SBUX'])
#new_portfolio.doMarkowitz()