import controller.config as config


class SafetyController:
    """Safety controller for maximum allowed speed based on odometry feedback."""

    def __init__(self, max_speed_m_s: float = 0.3):
        self.max_speed_m_s = max_speed_m_s
        self.max_wheel_rpm = self.max_speed_m_s * 60.0 / config.WHEEL_CIRCUMFERENCE

    def enforce_wheel_rpm(self, wheel_rpm: float) -> float:
        if wheel_rpm > self.max_wheel_rpm:
            return self.max_wheel_rpm
        if wheel_rpm < -self.max_wheel_rpm:
            return -self.max_wheel_rpm
        return wheel_rpm

    def enforce_speed_m_s(self, speed_m_s: float) -> float:
        if speed_m_s > self.max_speed_m_s:
            return self.max_speed_m_s
        if speed_m_s < -self.max_speed_m_s:
            return -self.max_speed_m_s
        return speed_m_s

    def check_odometry(self, odometry_data: dict) -> bool:
        if not odometry_data:
            return False
        return abs(odometry_data.get('speed_m_s', 0.0)) <= self.max_speed_m_s

    def safe_set_speed(self, odom, wheel_rpm_cmd: float) -> float:
        safe_rpm = self.enforce_wheel_rpm(wheel_rpm_cmd)
        if hasattr(odom, 'set_speed'):
            odom.set_speed(safe_rpm)
        return safe_rpm


class MotorController:
    """Motor controller wrapper for odometry and RPM commands."""

    def __init__(self, odom, safety_controller: SafetyController = None):
        self.odom = odom
        self.safety = safety_controller or SafetyController()

    def rpm_to_wheel_rpm(self, rpm: float) -> float:
        return rpm / config.POLE_PAIRS

    def wheel_rpm_to_rpm(self, wheel_rpm: float) -> float:
        return wheel_rpm * config.POLE_PAIRS

    def set_speed_rpm(self, wheel_rpm: float):
        # 1. Enforce safe limits (working in wheel RPM)
        safe_wheel_rpm = self.safety.enforce_wheel_rpm(wheel_rpm)
        
        # 2. Pass to odometry, which handles conversion to ERPM
        if hasattr(self.odom, 'set_speed'):
            self.odom.set_speed(safe_wheel_rpm)
            
        # Return informative ERPM value for UI (what VESC actually sees)
        return safe_wheel_rpm * config.GEAR_RATIO * config.POLE_PAIRS

    def set_speed_m_s(self, speed_m_s: float):
        safe_speed = self.safety.enforce_speed_m_s(speed_m_s)
        wheel_rpm = safe_speed * 60.0 / config.WHEEL_CIRCUMFERENCE
        return self.set_speed_rpm(wheel_rpm)

    def stop(self):
        return self.set_speed_rpm(0.0)

    def read_raw_data(self) -> dict:
        data = {
            'motor_rpm': 0,
            'wheel_rpm': 0,
            'distance_m': 0,
            'speed_m_s': 0,
            'voltage': 0,
            'tacho': 0,
        }

        if not self.odom:
            return data

        odom_data = self.odom.get_data() or {}

        data['wheel_rpm'] = odom_data.get('wheel_rpm', 0.0)
        data['motor_rpm'] = odom_data.get('raw_rpm', 0.0)
        data['distance_m'] = odom_data.get('distance_m', 0.0)
        data['speed_m_s'] = odom_data.get('speed_m_s', 0.0)
        data['voltage'] = odom_data.get('voltage', 0.0)
        data['tacho'] = odom_data.get('raw_tacho', 0.0)

        return data

    def reset_distance(self):
        if hasattr(self.odom, 'reset_distance'):
            return self.odom.reset_distance()

    def set_distance(self, new_distance_m: float):
        if hasattr(self.odom, 'set_distance'):
            return self.odom.set_distance(new_distance_m)

