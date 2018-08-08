from trade.strategy_base import StrategyParser


class EmaStrategy(StrategyParser):
    indicators_required = ['ema_fast', 'ema_slow', 'ichimoku_a', 'ichimoku_b']


    def should_open_position(self):
        last = self.df.iloc[-1]
        previous = self.df.iloc[-2]
        two_before = self.df.iloc[-3]

        if previous['ema_fast'] < previous['ema_slow']:
            if last['ema_fast'] > last['ema_slow']:
                return True, 'buy'
        elif previous['ema_fast'] > previous['ema_slow']:
            if last['ema_fast'] < last['ema_slow']:
                return True, 'sell'
        return False, False

    def should_close_position(self, order):

        # if self.opposite_candle(order.position):
        #     return True
        if self.price_moved_by_percentage(order.open_price):
            return True

    def opposite_candle(self, position):
        last = self.df.iloc[-1]
        if position == 'buy':
            if last['close'] < last['open']:
                return True
        elif position == 'sell':
            if last['close'] > last['open']:
                return True

    def price_moved_by_percentage(self, open_price):
        last = self.df.iloc[-1]
        percentage_more = open_price * 1.025
        percentage_less = open_price * 0.975
        if last['close'] > percentage_more or last['close'] < percentage_less:
            return True

    # rodzaje decyzji
# wskaznik przekroczyl cene
# wskaznik przekroczyl inny wskaznik
# pojawienie sie swiecy

# open conditions dictate what indicators to prepare
