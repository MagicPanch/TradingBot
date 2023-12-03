from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime  # For datetime objects
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])

# Import the backtrader platform
import backtrader as bt

class Bollinger(bt.Strategy):
    params = (
        ("period", 20),
        ("devfactor", 2.0),
        ("risk_factor", 0.02),  # Porcentaje del capital a arriesgar por operación
    )

    def __init__(self):
        self.bollinger = bt.indicators.BollingerBands(self.data.close, period=self.params.period, devfactor=self.params.devfactor)

    def next(self):
        if self.data.close > self.bollinger.lines.bot and not self.position:
            # Calcular el tamaño de la posición basado en el riesgo
            risk = self.broker.getvalue() * self.params.risk_factor
            size = risk / (self.data.close - self.bollinger.lines.bot)

            # Calcular el precio de stop loss
            stop_price = self.data.close * (1 - 0.02)  # Ejemplo: Stop loss al 2% por debajo del precio de entrada

            # Comprar con el tamaño calculado y establecer el stop loss
            self.buy(size=size, exectype=bt.Order.Stop, price=stop_price)

        elif self.data.close < self.bollinger.lines.top and self.position:
            # Vender toda la posición
            self.sell()
# Create a Stratey
class Cross_rsi_bollinger(bt.Strategy):
    params = (
        ('first_period', 2),
        ("short_period", 50),
        ("long_period", 200),
        ('rsi_period',10),
        ('rsi_overbought',65),
        ("rsi_oversold", 35),
        ("period", 10),
        ("devfactor", 2.0),
    )

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None

        self.short_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.short_period)
        self.long_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.long_period)
        self.crossover = bt.indicators.CrossOver(self.short_ma, self.long_ma)
        self.crossunder = bt.indicators.CrossDown(self.short_ma, self.long_ma)
        self.short_sma = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.first_period)
        self.rsi = bt.indicators.RelativeStrengthIndex(
            period=self.params.rsi_period)
        self.bollinger = bt.indicators.BollingerBands(self.data.close, period=self.params.period,
                                                      devfactor=self.params.devfactor)
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:

            # Not yet ... we MIGHT BUY if ...
            if   self.dataclose > self.short_sma and self.dataclose[-1] <= self.short_sma[-1] and self.rsi < self.params.rsi_oversold:

                # BUY, BUY, BUY!!! (with all possible default parameters)
                self.log('BUY CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.buy()

        elif self.crossunder > 0 or self.data.close < self.bollinger.lines.top and self.rsi > self.params.rsi_overbought:
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()

class Golden_Death_Cross(bt.Strategy):
    params = (
        ("short_period", 50),
        ("long_period", 200),
    )

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None

        # Add a MovingAverageSimple indicator

        self.short_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.short_period)
        self.long_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.long_period)
        self.crossover = bt.indicators.CrossOver(self.short_ma, self.long_ma)
        self.crossunder = bt.indicators.CrossDown(self.short_ma, self.long_ma)
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:

            # Not yet ... we MIGHT BUY if ...
            if self.crossover > 0:

                # BUY, BUY, BUY!!! (with all possible default parameters)
                self.log('BUY CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.buy()


        elif  self.crossunder > 0:
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()

if __name__ == '__main__':
    # Create a cerebro entity
    cerebro = bt.Cerebro()

    # Cross_rsi_bollinger_strategy
    idx = cerebro.addstrategy(Cross_rsi_bollinger)
    cerebro.addsizer_byidx(idx, bt.sizers.SizerFix, stake=1400)

    # Golden_Death_Cross strategy
    #idx2 =cerebro.addstrategy(Golden_Death_Cross)
    #cerebro.addsizer_byidx(idx2, bt.sizers.SizerFix, stake=1400)

    # Bollinger strategy
    #cerebro.addstrategy(Bollinger)

    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    datapath = os.path.join(modpath, '.\\datas\\orcl-1995-2014.txt')

    # Create a Data Feed
    data = bt.feeds.YahooFinanceCSVData(
        dataname=datapath,
        # Do not pass values before this date
        fromdate=datetime.datetime(2005, 1, 1),
        # Do not pass values before this date
        todate=datetime.datetime(2006, 12, 30),
        # Do not pass values after this date
        reverse=False)

    cerebro.adddata(data)
    # Set our desired cash start
    cerebro.broker.setcash(100000.0)
    cerebro.addsizer(bt.sizers.PercentSizer, percents=10)
    # Add a FixedSize sizer according to the stake
    #cerebro.addsizer(bt.sizers.FixedSize, stake=10)

    # Set the commission
    cerebro.broker.setcommission(commission=0.001)

    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run over everything
    cerebro.run()

    # Print out the final result
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

    cerebro.plot()