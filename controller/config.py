# Nastavení portu
SERIAL_PORT = "COM18"
BAUD_RATE = 115200

# Parametry motoru a mechaniky
POLE_PAIRS = 15        # Počet párů pólů motoru (ERPM = RPM * POLE_PAIRS)
GEAR_RATIO = 1.0      # Převodový poměr (1.0 = přímý náhon)
WHEEL_DIAMETER = 0.21  # Průměr kola v metrech (např. 0.1m = 10cm)

MAX_SPEED = 0.8 # in m/s

# Konstanty pro výpočet
import math
WHEEL_CIRCUMFERENCE = WHEEL_DIAMETER * math.pi
