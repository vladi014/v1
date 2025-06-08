import ccxt

class ExecutionEngine:
    def __init__(self, config, logger):
        exchange_cls = getattr(ccxt, config['api']['exchange'])
        self.exchange = exchange_cls({
            'apiKey': config['api']['api_key'],
            'secret': config['api']['api_secret'],
        })
        self.logger = logger

    def execute(self, signal):
        order = self.exchange.create_order(
            symbol=signal['symbol'],
            type='market',
            side=signal['side'],
            amount=signal['amount']
        )
        self.logger.info(f'Orden ejecutada: {order}')
