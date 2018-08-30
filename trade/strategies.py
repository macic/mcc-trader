from trade.strategy_base import StrategyParser


class EmaStrategy(StrategyParser):
    indicators_required = ['ema_fast', 'ema_slow']

    def should_open_position(self, **kwargs):
        last = self.df.iloc[-1]
        previous = self.df.iloc[-2]

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
    # BTC USD
    # n = 14
    # n_dev = 2.0
    # pinbar_min = 80
    # pinbar_perc = 35
    #
    # ETH EUR
    # n = [20, 22, 24]
    # n_dev = [1.7, 1.8, 1.9]
    # pinbar_min = 1.75
    # pinbar_perc = 15
    # tp = 6
    # sl = 3

    indicators_required = ['bollinger_hband', 'bollinger_lband']

    def should_open_position(self, **kwargs):
        last = self.df.iloc[-1]
        previous = self.df.iloc[-2]
        two_before = self.df.iloc[-3]

        is_pinbar, type_ = self.is_pinbar(last, **kwargs)
        if is_pinbar:
            if type_ == 'buy':
                if last['high'] <= last['bollinger_lband'] or (last['low'] <= last['bollinger_lband'] <= last['high']):
                    return True, type_
            elif type_ == 'sell':
                if last['low'] >= last['bollinger_hband'] or (last['low'] <= last['bollinger_hband'] <= last['high']):
                    return True, type_
        return False, False

    # def should_close_position(self, order, **kwargs):
    #
    #     if self.opposite_candle(order.position, check_two_candles=True):
    #         return True

    def should_close_position(self, order, **kwargs):

        tp_p = kwargs.get('take_profit_percentage') or 12
        sl_p = kwargs.get('trailing_stop_loss_percentage') or 2
        abs_sl = (sl_p / 100) * order.open_price

        if self.take_profit_percentage_with_trailing_stop_loss(order.open_price, order.position, float(tp_p),
                                                               float(abs_sl)):
            return True
