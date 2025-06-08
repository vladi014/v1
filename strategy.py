from abc import ABC, abstractmethod

class Strategy(ABC):
    def __init__(self, config):
        self.config = config

    @abstractmethod
    def generate_signal(self):
        """Debe retornar dict{'symbol','side','amount'} o None."""
        pass

class ExampleStrategy(Strategy):
    def generate_signal(self):
        # Ejemplo: sin lógica, siempre retorna None
        return None
