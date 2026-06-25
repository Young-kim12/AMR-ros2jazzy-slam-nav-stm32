import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import JointState
from command_center_msgs.msg import RobotState, SystemStatus
from command_center_hal.hal.stm32_hal import STM32HAL
from command_center_hal.hal.lidar_hal import LidarHAL


class RobotNode(Node):
    """
    COMMAND CENTER 메인 로봇 노드
    STM32 micro-ROS 토픽 기반
    """

    def __init__(self):
        super().__init__('robot_node')

        # HAL 초기화
        self.stm32 = STM32HAL()
        self.lidar = LidarHAL()
        self.stm32.initialize()
        self.lidar.initialize()

        # 파라미터
        self.declare_parameter('robot_id', 'AMR_01')
        self.declare_parameter('wheel_separation', 0.35)
        self.declare_parameter('wheel_radius', 0.05)
        self.declare_parameter('invert_left_motor', False)
        self.declare_parameter('invert_right_motor', True)

        self.robot_id = self.get_parameter('robot_id').value
        self.wheel_separation = self.get_parameter('wheel_separation').value
        self.wheel_radius = self.get_parameter('wheel_radius').value
        self.invert_left = self.get_parameter('invert_left_motor').value
        self.invert_right = self.get_parameter('invert_right_motor').value

        # Subscriber
        self.cmd_vel_sub = self.create_subscription(
            Twist, 'cmd_vel', self.cmd_vel_callback, 10)

        # Publisher
        
        self.robot_state_pub = self.create_publisher(RobotState, 'robot_state', 10)
        self.system_status_pub = self.create_publisher(SystemStatus, 'system_status', 10)

        # STM32로 모터 명령 전송 (JointState 타입)
        self.joint_cmd_pub = self.create_publisher(
            JointState, '/cmd_joint_states', 10)

        # 타이머

        self.status_timer = self.create_timer(1.0, self.status_callback)

        self.get_logger().info(f'[{self.robot_id}] RobotNode 시작')

    def cmd_vel_callback(self, msg: Twist):
        """cmd_vel 수신 → 차동 구동 역운동학 → STM32로 JointState 전송"""
        linear = msg.linear.x
        angular = msg.angular.z

        # 차동 구동 역운동학 변환 (m/s 기준 바퀴 속도)
        left_ms = linear + (angular * self.wheel_separation / 2.0)
        right_ms = linear - (angular * self.wheel_separation / 2.0)

        # rad/s 변환 (STM32는 rad/s를 기대한다고 가정)
        left_rads = left_ms / self.wheel_radius
        right_rads = right_ms / self.wheel_radius

        # 모터 방향 반전 보정 (예: 물리적으로 반대로 장착된 경우)
        left_cmd = -left_rads if self.invert_left else left_rads
        right_cmd = -right_rads if self.invert_right else right_rads

        # STM32HAL 업데이트
        self.stm32.set_motor_speed(left_cmd, right_cmd)

        # /cmd_joint_states 퍼블리시 (STM32가 구독)
        joint_cmd = JointState()
        joint_cmd.header.stamp = self.get_clock().now().to_msg()
        joint_cmd.name = ['left_wheel_joint', 'right_wheel_joint']
        joint_cmd.velocity = [left_cmd, right_cmd]
        self.joint_cmd_pub.publish(joint_cmd)

        self.get_logger().info(
            f'모터 명령 | 좌: {left_cmd:.2f} rad/s | 우: {right_cmd:.2f} rad/s')


    def status_callback(self):
        """로봇 상태 및 시스템 상태 퍼블리시"""
        robot_state = RobotState()
        robot_state.robot_id = self.robot_id
        robot_state.battery_voltage = 12.0
        robot_state.battery_percentage = 100.0
        robot_state.is_emergency_stop = False
        left, right = self.stm32.get_motor_speed()
        robot_state.linear_velocity = (left + right) / 2.0
        robot_state.angular_velocity = (right - left) / 2.0
        robot_state.timestamp = self.get_clock().now().to_msg()
        self.robot_state_pub.publish(robot_state)

        system_status = SystemStatus()
        system_status.stm32_connected = self.stm32.is_connected()
        system_status.lidar_connected = self.lidar.is_connected()
        system_status.camera_connected = False
        system_status.error_message = ''
        system_status.system_state = 0
        self.system_status_pub.publish(system_status)

    def destroy_node(self):
        self.stm32.shutdown()
        self.lidar.shutdown()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = RobotNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()