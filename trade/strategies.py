from trade.strategy_base import StrategyParser


class EmaStrategy(StrategyParser):
    indicators_required = ['ema_fast', 'ema_slow', 'ichimoku_a', 'ichimoku_b']

    def should_open_position(self, **kwargs):
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

    def should_close_position(self, order, **kwargs):

        tp_p = kwargs.get('take_profit_percentage') or 7.5
        sl_p = kwargs.get('stop_loss_percentage') or 2
        if self.price_moved_by_percentage(order.open_price, order.position, float(tp_p), float(sl_p)):
            return True

class BBPinbarStrategy(StrategyParser):
    indicators_required = ['ema_fast', 'ema_slow', 'ichimoku_a', 'ichimoku_b']

    def should_open_position(self, **kwargs):
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

    def should_close_position(self, order, **kwargs):

        tp_p = kwargs.get('take_profit_percentage') or 7.5
        sl_p = kwargs.get('stop_loss_percentage') or 2
        if self.price_moved_by_percentage(order.open_price, order.position, float(tp_p), float(sl_p)):
            return True

    # rodzaje decyzji
# wskaznik przekroczyl cene
# wskaznik przekroczyl inny wskaznik
# pojawienie sie swiecy

# open conditions dictate what indicators to prepare
