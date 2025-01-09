# Imports to add the trade master directory in search path
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import to elimate unnecessary warnings
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
import math

# Import the Strategy class from backtesting. Any strategy class will inherit this class
from TradeMaster.backtesting import Strategy

# Import the trade management and risk management startegies to be used in the strategy.
from TradeMaster.trade_management.atr_tm import ATR_RR_TradeManagement
from TradeMaster.risk_management.cppi_rm import CPPIRiskManagement

# Import the multibacktester for performing the backtest.
from TradeMaster.multi_backtester.multi_backtester import MultiBacktest

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
        self.trade_management_strategy = ATR_RR_TradeManagement(self,self.risk_reward_ratio,self.atr_multiplier,self.atr_period) # Just pass the strategy object in the trade mgt class
        self.risk_management_strategy = EqualRiskManagement(self,self.initial_risk_per_trade) # Just pass the strategy object in the risk mgt class
        
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
        
if __name__ == '__main__':
    '''
    First create an object of the the Multibacktest class. 
    At time of instantiation, specify the strategy class as the first argument.
    Thereafter, additional keyword arguments can be supplied as is the case in backtesting.py.
    These include: cash, commission, holding, margin, trade_on_close, hedging, exclusive_orders, 
    trade_start_date, lot_size, fail_fast, storage, is_option 
    '''
    bt = MultiBacktest(AdxTrendStrategy, cash = 100000, commission = 0.002, margin = 1/100)
    
    '''
    Thereafter, to backtest a single stock on all timeframes, specify the stock name, timeframe = 'all',
    market name, exchange name.
    The exchange name is optional and if not specified, the default exchange for the market is used.
    Additonal keyword arguments can be specified as well which are the optional arguments given in the 
    backtesting.run() function.
    The output is saved in a separate directory the path of which will be printed.
    The output will consist of two parts:
    1. The stats of the run in a single excel sheet, one entry for each timeframe. 
    2. The tearsheets, one for each timeframe used as per the data available in the db.
    '''
    bt.backtest_stock("AAPL", "all", "us", "firstratedata")
    
    