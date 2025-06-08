import ccxt

class ExecutionEngine:
    def __init__(self, config, logger):
        exchange_cls = getattr(ccxt, config['api']['exchange'])
        self.exchange = exchange_cls({
            'apiKey': config['api']['api_key'],
            'secret': config['api']['api_secret'],
            'enableRateLimit': True,
        })
        self.logger = logger

    def execute(self, signal):
        try:
            order = self.exchange.create_order(
                symbol=signal['symbol'],
                type='market',
                side=signal['side'],
                amount=signal['amount']
            )
            self.logger.info(f'Orden ejecutada: {order}')
        except Exception as e:
            self.logger.error(f'Error al ejecutar orden: {e}')
