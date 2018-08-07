from trade.strategy_base import StrategyParser

class EmaStrategy(StrategyParser):

    indicators_required = ['ema_fast', 'ema_slow', 'ichimoku_a', 'ichimoku_b']

    #rodzaje decyzji
# wskaznik przekroczyl cene
# wskaznik przekroczyl inny wskaznik
# pojawienie sie swiecy

# open conditions dictate what indicators to prepare