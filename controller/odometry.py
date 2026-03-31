from pyvesc import VESC
import controller.config as config
import time

class VescControll:
    def __init__(self):
        self.serial_port = config.SERIAL_PORT
        self.baudrate = config.BAUD_RATE
        self.vesc = None
        self._tacho_zero = 0
        self._last_data = None

    def connect(self):
        try:
            if self.serial_port is None:
                print("Chyba: Port není definován v config.py")
                return False

            # Přidáme start_heartbeat=False, aby se neprala vlákna při inicializaci
            self.vesc = VESC(serial_port=self.serial_port, baudrate=self.baudrate, start_heartbeat=False)
            time.sleep(0.5) 

            for i in range(5):
                print(f"Pokus o čtení dat {i+1}/5...")
                data = self.get_data() # Teď už metoda existuje níže
                if data:
                    self._tacho_zero = data['raw_tacho']
                    print("VESC komunikuje správně.")
                    return True
                time.sleep(0.5)

            if self.vesc:
                print("VESC připojen, ale telemetrie zatím neodpovídá.")
                return True 
            return False
        except Exception as e:
            print(f"Chyba připojení k VESC: {e}")
            return False

    # TATO METODA TI CHYBĚLA:
    def get_data(self):
        if not self.vesc:
            return None
        try:
            data = self.vesc.get_measurements()
            if data:
                rpm_raw = getattr(data, 'rpm', 0)
                tacho_raw = getattr(data, 'tachometer', 0)
                voltage = getattr(data, 'v_in', 0)

                # Přepočty
                wheel_rpm = rpm_raw / (config.POLE_PAIRS * config.GEAR_RATIO)
                wheel_speed_ms = (wheel_rpm * config.WHEEL_CIRCUMFERENCE) / 60.0
                
                # Odometrie (relativní od startu nebo resetu)
                odo_rotations = (tacho_raw - self._tacho_zero) / (config.POLE_PAIRS * config.GEAR_RATIO)
                odo_distance_m = odo_rotations * config.WHEEL_CIRCUMFERENCE

                self._last_data = {
                    'motor_rpm': rpm_raw,
                    'wheel_rpm': wheel_rpm,
                    'raw_tacho': tacho_raw,
                    'tacho': tacho_raw - self._tacho_zero,
                    'distance_m': odo_distance_m,
                    'voltage': voltage,
                    'speed_m_s': wheel_speed_ms,
                }
                return self._last_data
        except Exception as e:
            print(f"Chyba při čtení dat: {e}")
        return None

    def _to_tacho_raw(self, wheel_distance_m):
        rotations = wheel_distance_m / config.WHEEL_CIRCUMFERENCE
        return rotations * config.POLE_PAIRS * config.GEAR_RATIO

    def get_last_data(self):
        return self._last_data

    def reset_distance(self):
        data = self.get_data()
        if data:
            self._tacho_zero = data['raw_tacho']

    def set_distance(self, new_distance_m):
        data = self.get_data()
        if data:
            current_tacho = data['raw_tacho']
            # Vypočítáme offset tak, aby ujetá vzdálenost odpovídala zadání
            self._tacho_zero = current_tacho - self._to_tacho_raw(new_distance_m)

    def set_speed(self, wheel_rpm):
        if self.vesc:
            try:
                target_erpm = int(wheel_rpm * config.GEAR_RATIO * config.POLE_PAIRS)
                print(target_erpm)
                self.vesc.set_rpm(target_erpm)
                return target_erpm
            except Exception:
                print("Error in set_speed")
                pass
        return 0

    def set_speed_m_s(self, m_s):
        wheel_rpm = (m_s * 60.0) / config.WHEEL_CIRCUMFERENCE
        return self.set_speed(wheel_rpm)

    def stop(self):
        if self.vesc:
            self.vesc.set_rpm(0)

    def close(self):
        if self.vesc:
            try:
                self.vesc.set_rpm(0)
                if self.vesc.serial_port:
                    self.vesc.serial_port.close()
                self.vesc = None
            except:
                pass
            