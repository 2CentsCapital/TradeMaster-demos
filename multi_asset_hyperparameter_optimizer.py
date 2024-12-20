# Imports to add the trade master directory in search path
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import to elimate unnecessary warnings
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
import math
import talib as ta
from TradeMaster.lib import crossover

# Import the Strategy class from backtesting. Any strategy class will inherit this class
from TradeMaster.backtesting import Strategy

# Import the hyperparameter optimiser.
from TradeMaster.hyperparameter_optimizer.hyperparameter_optimizer import HyperParameterOptimizer

'''
Define the strategy as is done in usual backtesting.py library
'''

class MovingAverageCrossover2(Strategy):
    sma_short = 20
    sma_long = 50
    dummy = 100

    def init(self):
        self.sma_short = self.I(ta.SMA, self.data.Close, timeperiod=self.sma_short)
        self.sma_long = self.I(ta.SMA, self.data.Close, timeperiod=self.sma_long)

    def next(self):
        if crossover(self.sma_short, self.sma_long):
            self.buy()
        elif crossover(self.sma_long, self.sma_short):
            self.position().close()
    
'''
Always use the __name__ == '__main__' guard. Else there will be issues with multiprocessing.
'''    
        
def sma_constraint(p):
    return p['sma_short'] < p['sma_long']   
        
if __name__ == '__main__':
    '''
    The optimization is performed wrt three metrics:
    1. Sharpe Ratio
    2. Equity Final
    3. Win Rate
    '''
    
    '''
    First create an object of the the HyperParameterOptimizer class. 
    At time of instantiation, specify the strategy class.
    
    All the other optional parameters available in the multibacktester
    such as cash, commission, etc. can be specified as keyword args here.
    '''
    bt = HyperParameterOptimizer(MovingAverageCrossover2, cash=100000, commission=.002)
    
    '''
    Thereafter, to find the optimal parameter combination for the strategy for each stock in
    universe separately, use the optimize_universe function.
    Provide universe, timeframe and exchange(optional) as arguments.
    Working identical to Backtest.optimize in backtesting.py.
    Thereafter, provide the parameters to optimise as keyword arguments separately. These parameters must be
    defined in the strategy class as global parameters. If there is any constraint function to omit some 
    parameter combination, provide that as well. Do not use lambdas due to problems with multiprocessing.

    Other optional parameters that can be provided as keyword args include: max_tries(Use incase of too many
    possible combinations of the optimizing parameters), optimization method and random state(these two rarely used).
    The output gets saved in a separate directory whose path will get printed. Refer to it.
    The output is a summary excel sheet for each stock.
    The summary excel sheet: This will consist of 3 separate subsheets, one each for the 3 metrics of optimization.
    For each metric, the top 10 percentile settings of the parameters and the corresponding metric value is present as 
    a table. Therafter, all possible heatmaps are plotted taking all pairs of the optimization parameters.
    For any pair of parameters, other parameters can take various values. All of them are considered and the metric is averaged
    out over all of these results.
    '''
    bt.optimize_universe('S&P 500', '1day', 'firstratedata', 
    constraint=sma_constraint, sma_short = range(10,100,30), sma_long = range(40,150,40))
    