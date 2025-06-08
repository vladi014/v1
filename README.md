# Plantilla de Bot de Trading

Este proyecto proporciona una base sólida para un bot de trading automatizado.  
Estructura:

```
trading_bot_template/
├── bot.py
├── config.yml
├── config.py
├── strategy.py
├── execution.py
├── logger.py
├── backtest.py
├── requirements.txt
└── README.md
```

## Archivos principales

- **bot.py**: Punto de entrada; carga configuración, inicializa estrategia y ejecución.
- **config.yml**: Parámetros de API y bot (símbolo, timeframe, gestión de riesgo).
- **config.py**: Función para cargar archivos YAML.
- **strategy.py**: Clase abstracta `Strategy` y ejemplo de estrategia.
- **execution.py**: Motor de ejecución usando CCXT para órdenes de mercado.
- **logger.py**: Configuración de logging.
- **backtest.py**: Plantilla para futuras funcionalidades de backtesting.

## Uso

1. Instalar dependencias:
   ```
   pip install -r requirements.txt
   ```
2. Configurar `config.yml` con tus credenciales y parámetros.
3. Ejecutar:
   ```
   python bot.py
   ```