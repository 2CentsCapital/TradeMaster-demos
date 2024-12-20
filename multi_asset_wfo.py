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

# Import the trade management and risk management startegies to be used in the strategy.
from TradeMaster.trade_management.atr_tm import ATR_RR_TradeManagement
from TradeMaster.risk_management.equal_weigh_rm import EqualRiskManagement

# Import the walk forward optimiser.
from TradeMaster.wfo import WalkForwardOptimizer

'''
Define the strategy as is done in usual backtesting.py library
'''

class AdxTrendStrategy(Strategy):
    atr_period = 14
    risk_reward_ratio = 1.25
    atr_multiplier = 3
    initial_risk_per_trade = 0.01
    adx_period=14

    def init(self):
        self.adx = self.I(self.data.df.ta.adx(self.adx_period)[f"ADX_{self.adx_period}"])
        self.trade_management_strategy = ATR_RR_TradeManagement(self) # Just pass the strategy object in the trade mgt class
        self.risk_management_strategy = EqualRiskManagement(self) # Just pass the strategy object in the risk mgt class
        self.total_trades = len(self.closed_trades)

    def next(self):
        self.on_trade_close()
        
        if self.adx[-1] > 25:
            if self.data.Close[-1] > self.data.Close[-2]:
                if self.position().is_short:
                    self.position().close()
                if not self.position():
                    self.add_buy_trade()
            elif self.data.Close[-1] < self.data.Close[-2]:
                if self.position().is_long:
                    self.position().close()
                if not self.position():
                    self.add_sell_trade()

    def add_buy_trade(self):
        risk_per_trade = self.risk_management_strategy.get_risk_per_trade()
        entry = self.data.Close[-1]
        if risk_per_trade > 0:
            stop_loss, take_profit = self.trade_management_strategy.calculate_tp_sl(direction="buy")
            stop_loss_perc = (entry - stop_loss) / entry
            trade_size = risk_per_trade / stop_loss_perc
            qty = math.ceil(trade_size / self.data.Close[-1])
            self.buy(size=qty, sl=stop_loss, tp=take_profit)

    def add_sell_trade(self):
        risk_per_trade = self.risk_management_strategy.get_risk_per_trade()
        entry = self.data.Close[-1]
        if risk_per_trade > 0:
            stop_loss, take_profit = self.trade_management_strategy.calculate_tp_sl(direction="sell")
            stop_loss_perc = (stop_loss - entry) / entry
            trade_size = risk_per_trade / stop_loss_perc 
            qty = math.ceil(trade_size / self.data.Close[-1]) 
            self.sell(size=qty, sl=stop_loss, tp=take_profit)

    def on_trade_close(self):
        num_of_trades_closed = len(self.closed_trades) - self.total_trades
        if num_of_trades_closed > 0:
            for trade in self.closed_trades[-num_of_trades_closed:]:
                if trade.pl < 0:
                    # Parameter update in case strategy suffers a loss
                    self.risk_management_strategy.update_after_loss() 
                else:
                    # Parameter update in case strategy make a profit
                    self.risk_management_strategy.update_after_win() 
        self.total_trades = len(self.closed_trades)
    
'''
Always use the __name__ == '__main__' guard. Else there will be issues with multiprocessing.
'''    
        
def constraint_function(p): # A dummy constraint always true here
    return p['adx_period'] > 10        
        
if __name__ == '__main__':
    '''
    First create an object of the the WalkForwardOptimizer class. 
    At time of instantiation, specify the strategy class, optimization parameters, constraints and then 
    maximize metric. The terms have their usual meanings as in backtesting.py
    
    constraints is optional.
    
    If maximize is not specified, it is taken as Equity Final by default.
    
    Do not use lambda expressions for the constraint. Rather, use normal functions.
    Lambda functions are not pickable and cannot be used in multiprocessing. 
    
    Provide the optimization parameters as a dictionary as shown here.
    
    Apart from these parameters, all the other optional parameters available in the multibacktester
    such as cash, commission, etc. can be specified as keyword args here.
    '''
    optimization_params = {
        'adx_period' : range(12,20,2)
    }
    optimizer = WalkForwardOptimizer(AdxTrendStrategy, optimization_params, constraint_function , 
                                     'Sharpe Ratio', 
                                     cash = 100000, commission=.002, margin = 1/100)
    
    '''
    Thereafter, to optimise on all stocks in a universe, specify the universe name, timeframe and the exchange name.
    The exchange name is optional and if not specified, the default exchange for the market is used.
    Then provide training prd and testing prd for WFO.
    The exchange name is optional and if not specified, the default exchange for the market is used.
    training period defaults to 3M and testing period to 1M. Use M, H, D for months, hours, days respectively. 
    The output gets saved in a separate directory whose path will get printed. Refer to it.
    The output will consist of two parts:
    1. Summary sheets for all stocks in an excel sheet
    2. Tearsheets for all stocks 
    '''
    optimizer.optimize_universe('S&P 500', '1day', 'firstratedata', '6M', '2M')
    