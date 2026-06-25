from command_center_hal.hal.base_hal import BaseHAL


class LidarHAL(BaseHAL):
    """
    YDLiDAR 하드웨어 추상화 레이어
    실제 환경에서는 YDLiDAR SDK로 교체
    """

    def __init__(self):
        self._connected = False
        self._scan_data = []
        self._port = '/dev/ydlidar'

    def initialize(self) -> bool:
        """YDLiDAR 초기화"""
        # 실제 환경:
        # import ydlidar
        # ydlidar.os_init()
        # self.laser = ydlidar.CYdLidar()
        # self.laser.setlidaropt(ydlidar.LidarPropSerialPort, self._port)
        self._connected = True
        print(f'[LidarHAL] YDLiDAR 초기화 완료 | 포트: {self._port}')
        return True

    def shutdown(self) -> None:
        """YDLiDAR 종료"""
        # 실제 환경: self.laser.turnOff()
        self._connected = False
        print('[LidarHAL] YDLiDAR 종료')

    def is_connected(self) -> bool:
        return self._connected

    def get_scan(self) -> list:
        """
        스캔 데이터 반환
        실제 환경: YDLiDAR SDK에서 실제 스캔 데이터 반환
        """
        if not self._connected:
            print('[LidarHAL] 연결 안됨')
            return []

        import math
        self._scan_data = [
            {'angle': i, 'distance': 1.0 + 0.1 * math.sin(math.radians(i))}
            for i in range(360)
        ]
        return self._scan_data