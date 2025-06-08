from abc import ABC, abstractmethod
import ccxt
import numpy as np
import pandas as pd
from ta.trend import ADXIndicator
from ta.volatility import BollingerBands

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
    """Selecciona la mejor estrategia según el régimen de mercado."""
    def __init__(self, config):
        super().__init__(config)
        self.trend = TrendFollowingStrategy(config)
        self.grid = GridTradingStrategy(config)
        self.mean = MeanReversionStrategy(config)
        strat_cfg = config["bot"].get("strategy", {})
        self.adx_period = strat_cfg.get("adx_period", 14)
        self.adx_trend = strat_cfg.get("adx_trend", 25)
        self.bb_period = strat_cfg.get("bb_period", 20)
        self.bb_dev = strat_cfg.get("bb_dev", 2)
        self.bbw_high = strat_cfg.get("bbw_high", 0.05)
        self.bbw_low = strat_cfg.get("bbw_low", 0.02)
        # Alias para compatibilidad con documentación anterior
        self.threshold = strat_cfg.get("auto_trend_threshold", self.adx_trend)

    def _detect_state(self):
        limit = max(self.adx_period, self.bb_period, self.trend.long_window, self.mean.period) + 1
        try:
            ohlcv = self.trend.exchange.fetch_ohlcv(
                self.trend.symbol, timeframe=self.trend.timeframe, limit=limit
            )
        except Exception:
            return "grid"
        df = pd.DataFrame(ohlcv, columns=["time", "open", "high", "low", "close", "volume"])
        adx_ind = ADXIndicator(df["high"], df["low"], df["close"], window=self.adx_period)
        df["adx"] = adx_ind.adx()
        bb = BollingerBands(df["close"], window=self.bb_period, window_dev=self.bb_dev)
        df["bbw"] = (bb.bollinger_hband() - bb.bollinger_lband()) / bb.bollinger_mavg()
        adx_latest = df["adx"].iloc[-1]
        bbw_latest = df["bbw"].iloc[-1]
        if adx_latest > self.threshold:
            return "trend"
        if adx_latest <= self.threshold and bbw_latest > self.bbw_high:
            return "grid"
        if adx_latest <= self.threshold and bbw_latest <= self.bbw_low:
            return "mean"
        return None

    def generate_signal(self):
        state = self._detect_state()
        if state == "trend":
            return self.trend.generate_signal()
        if state == "grid":
            return self.grid.generate_signal()
        if state == "mean":
            return self.mean.generate_signal()
        return None
