from abc import ABC, abstractmethod


class BaseHAL(ABC):
    """
    HAL 추상 기본 클래스
    모든 하드웨어 드라이버는 이 클래스를 상속해야 해요
    """

    @abstractmethod
    def initialize(self) -> bool:
        """하드웨어 초기화"""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """하드웨어 종료"""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """연결 상태 확인"""
        pass