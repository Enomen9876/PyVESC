# Serial port settings
SERIAL_PORT = "COM18"
BAUD_RATE = 115200

# Setup the 


# Motor and mechanics parameters
POLE_PAIRS = 15       # Number of motor pole pairs (ERPM = RPM * POLE_PAIRS)
TACHO_FACTOR = 6 # 6*15 counts/rev
GEAR_RATIO = 1.0      # Gear ratio (1.0 = direct drive)
WHEEL_DIAMETER = 0.21  # Wheel diameter in meters (e.g. 0.1m = 10cm)

MAX_SPEED = 0.8 # in m/s

# Calculation constants
import math
WHEEL_CIRCUMFERENCE = WHEEL_DIAMETER * math.pi
