from command_center_hal.hal.base_hal import BaseHAL


class STM32HAL(BaseHAL):
    """
    STM32 하드웨어 추상화 레이어
    micro-ROS /cmd_joint_states 토픽으로 모터 제어
    """

    def __init__(self):
        self._connected = False
        self._left_speed = 0.0
        self._right_speed = 0.0
        self._port = '/dev/ttyUSB0'
        self._baudrate = 115200

    def initialize(self) -> bool:
        self._connected = True
        print(f'[STM32HAL] 초기화 완료 | 포트: {self._port}')
        return True

    def shutdown(self) -> None:
        self.set_motor_speed(0.0, 0.0)
        self._connected = False
        print('[STM32HAL] 종료')

    def is_connected(self) -> bool:
        return self._connected

    def set_motor_speed(self, left: float, right: float) -> None:
        if not self._connected:
            print('[STM32HAL] 연결 안됨')
            return
        self._left_speed = left
        self._right_speed = right

    def get_motor_speed(self) -> tuple:
        return self._left_speed, self._right_speed

    def emergency_stop(self) -> None:
        self.set_motor_speed(0.0, 0.0)
        print('[STM32HAL] 비상 정지!')