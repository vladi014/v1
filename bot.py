import time
import logging
from config import load_config
from strategy import (
    TrendFollowingStrategy,
    GridTradingStrategy,
    MeanReversionStrategy,
    AutoStrategy,
)
from execution import ExecutionEngine
from logger import setup_logger

def main():
    config = load_config('config.yml')
    logger = setup_logger()
    strat_cfg = config['bot'].get('strategy', {})
    name = strat_cfg.get('name', 'trend')
    if name == 'grid':
        strategy = GridTradingStrategy(config)
    elif name == 'mean':
        strategy = MeanReversionStrategy(config)
    elif name == 'auto':
        strategy = AutoStrategy(config)
    else:
        strategy = TrendFollowingStrategy(config)
    executor = ExecutionEngine(config, logger)

    logger.info('Bot de trading iniciado')
    while True:
        try:
            signal = strategy.generate_signal()
            if signal:
                executor.execute(signal)
        except Exception as e:
            logger.error(f'Error en bucle principal: {e}')
        time.sleep(config['bot']['timeframe_seconds'])

if __name__ == '__main__':
    main()
