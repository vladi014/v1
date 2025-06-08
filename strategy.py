from abc import ABC, abstractmethod
import ccxt
import numpy as np

class Strategy(ABC):
    def __init__(self, config):
        self.config = config

    @abstractmethod
    def generate_signal(self):
        """Debe retornar dict{'symbol','side','amount'} o None."""
        pass

class TrendFollowingStrategy(Strategy):
    def __init__(self, config):
        super().__init__(config)
        exchange_cls = getattr(ccxt, config['api']['exchange'])
        self.exchange = exchange_cls({
            'apiKey': config['api']['api_key'],
            'secret': config['api']['api_secret'],
        })
        self.symbol = config['bot']['symbol']
        self.timeframe = config['bot']['timeframe']
        strat_cfg = config['bot'].get('strategy', {})
        self.short_window = strat_cfg.get('short_window', 5)
        self.long_window = strat_cfg.get('long_window', 20)
        self.position = None

    def generate_signal(self):
        limit = self.long_window + 1
        try:
            ohlcv = self.exchange.fetch_ohlcv(self.symbol, timeframe=self.timeframe, limit=limit)
        except Exception:
            return None
        close_prices = [c[4] for c in ohlcv]
        short_sma = np.mean(close_prices[-self.short_window:])
        long_sma = np.mean(close_prices[-self.long_window:])

        if short_sma > long_sma and self.position != 'long':
            self.position = 'long'
            amount = self.config['bot']['risk']['max_position_size']
            return {'symbol': self.symbol, 'side': 'buy', 'amount': amount}
        elif short_sma < long_sma and self.position != 'short':
            self.position = 'short'
            amount = self.config['bot']['risk']['max_position_size']
            return {'symbol': self.symbol, 'side': 'sell', 'amount': amount}
        return None

class GridTradingStrategy(Strategy):
    """Estrategia simple de grid trading."""
    def __init__(self, config):
        super().__init__(config)
        exchange_cls = getattr(ccxt, config['api']['exchange'])
        self.exchange = exchange_cls({
            'apiKey': config['api']['api_key'],
            'secret': config['api']['api_secret'],
        })
        self.symbol = config['bot']['symbol']
        self.timeframe = config['bot']['timeframe']
        strat_cfg = config['bot'].get('strategy', {})
        self.lower = strat_cfg.get('grid_lower', 50000)
        self.upper = strat_cfg.get('grid_upper', 60000)
        self.step = strat_cfg.get('grid_step', 500)
        self.grid = list(np.arange(self.lower, self.upper + self.step, self.step))
        self.last_level = None

    def _current_level(self, price):
        levels = [lvl for lvl in self.grid if lvl <= price]
        return levels[-1] if levels else self.grid[0]

    def generate_signal(self):
        try:
            ohlcv = self.exchange.fetch_ohlcv(self.symbol, timeframe=self.timeframe, limit=2)
        except Exception:
            return None
        price = ohlcv[-1][4]
        level = self._current_level(price)
        if self.last_level is None:
            self.last_level = level
            return None
        amount = self.config['bot']['risk']['max_position_size']
        if level > self.last_level:
            self.last_level = level
            return {'symbol': self.symbol, 'side': 'sell', 'amount': amount}
        elif level < self.last_level:
            self.last_level = level
            return {'symbol': self.symbol, 'side': 'buy', 'amount': amount}
        return None

class MeanReversionStrategy(Strategy):
    """Estrategia simple de reversión a la media basada en RSI."""
    def __init__(self, config):
        super().__init__(config)
        exchange_cls = getattr(ccxt, config['api']['exchange'])
        self.exchange = exchange_cls({
            'apiKey': config['api']['api_key'],
            'secret': config['api']['api_secret'],
        })
        self.symbol = config['bot']['symbol']
        self.timeframe = config['bot']['timeframe']
        strat_cfg = config['bot'].get('strategy', {})
        self.period = strat_cfg.get('rsi_period', 14)
        self.overbought = strat_cfg.get('overbought', 70)
        self.oversold = strat_cfg.get('oversold', 30)

    def _rsi(self, prices):
        deltas = np.diff(prices)
        ups = np.where(deltas > 0, deltas, 0)
        downs = np.where(deltas < 0, -deltas, 0)
        roll_up = np.mean(ups[-self.period:])
        roll_down = np.mean(downs[-self.period:])
        rs = roll_up / (roll_down + 1e-9)
        return 100 - (100 / (1 + rs))

    def generate_signal(self):
        limit = self.period + 1
        try:
            ohlcv = self.exchange.fetch_ohlcv(self.symbol, timeframe=self.timeframe, limit=limit)
        except Exception:
            return None
        prices = [c[4] for c in ohlcv]
        rsi = self._rsi(prices)
        amount = self.config['bot']['risk']['max_position_size']
        if rsi > self.overbought:
            return {'symbol': self.symbol, 'side': 'sell', 'amount': amount}
        elif rsi < self.oversold:
            return {'symbol': self.symbol, 'side': 'buy', 'amount': amount}
        return None

class AutoStrategy(Strategy):
    """Selecciona la mejor estrategia según el estado del mercado."""
    def __init__(self, config):
        super().__init__(config)
        self.trend = TrendFollowingStrategy(config)
        self.grid = GridTradingStrategy(config)
        self.mean = MeanReversionStrategy(config)
        strat_cfg = config["bot"].get("strategy", {})
        self.threshold = strat_cfg.get("auto_trend_threshold", 0.01)

    def _detect_state(self):
        limit = max(self.trend.long_window, self.mean.period) + 1
        try:
            ohlcv = self.trend.exchange.fetch_ohlcv(self.trend.symbol, timeframe=self.trend.timeframe, limit=limit)
        except Exception:
            return "grid"
        prices = [c[4] for c in ohlcv]
        short_sma = np.mean(prices[-self.trend.short_window:])
        long_sma = np.mean(prices[-self.trend.long_window:])
        diff = abs(short_sma - long_sma) / (long_sma + 1e-9)
        deltas = np.diff(prices[-(self.mean.period + 1):])
        ups = np.where(deltas > 0, deltas, 0)
        downs = np.where(deltas < 0, -deltas, 0)
        roll_up = np.mean(ups[-self.mean.period:])
        roll_down = np.mean(downs[-self.mean.period:])
        rs = roll_up / (roll_down + 1e-9)
        rsi = 100 - (100 / (1 + rs))
        if diff > self.threshold:
            return "trend"
        if rsi > self.mean.overbought or rsi < self.mean.oversold:
            return "mean"
        return "grid"

    def generate_signal(self):
        state = self._detect_state()
        if state == "trend":
            return self.trend.generate_signal()
        elif state == "mean":
            return self.mean.generate_signal()
        return self.grid.generate_signal()
