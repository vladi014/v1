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
- **strategy.py**: Contiene la clase abstracta `Strategy` y varias estrategias
  de ejemplo listas para usar.
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
4. Selecciona la estrategia en `config.yml` dentro de `bot.strategy.name`.
   Las disponibles son `trend`, `grid`, `mean` y `auto`.
   - **trend**: seguimiento de tendencia usando medias móviles.
     Ajusta `short_window` y `long_window`.
   - **grid**: grid trading dentro de un rango con `grid_lower`,
     `grid_upper` y `grid_step`.
   - **mean**: reversión a la media con RSI; configura
     `rsi_period`, `overbought` y `oversold`.
   - **auto**: selección dinámica de estrategia según el mercado.
     Ajusta `auto_trend_threshold` para determinar cuándo considerar tendencia.
   No olvides rellenar tus claves de API.

## Advertencia

Este proyecto es un ejemplo educativo. Opera bajo tu propia responsabilidad.
