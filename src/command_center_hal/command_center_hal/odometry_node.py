from math import sin, cos, pi
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from geometry_msgs.msg import TransformStamped
from sensor_msgs.msg import JointState
from tf2_ros import TransformBroadcaster
import math

class OdometryNode(Node):

    def __init__(self):
        super().__init__('odometry_node')

        self.declare_parameter('wheel_separation', 0.20)
        self.declare_parameter('wheel_radius', 0.0325)
        self.declare_parameter('odom_frame', 'odom')
        self.declare_parameter('base_frame', 'base_link')
        self.declare_parameter('base_footprint_frame', 'base_footprint')
        self.declare_parameter('invert_left_motor', False)
        self.declare_parameter('invert_right_motor', False)

        self.wheel_separation = self.get_parameter('wheel_separation').value
        self.wheel_radius = self.get_parameter('wheel_radius').value
        self.odom_frame = self.get_parameter('odom_frame').value
        self.base_frame = self.get_parameter('base_frame').value
        self.base_footprint_frame = self.get_parameter('base_footprint_frame').value
        self.invert_left = self.get_parameter('invert_left_motor').value
        self.invert_right = self.get_parameter('invert_right_motor').value

        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        self.left_vel = 0.0
        self.right_vel = 0.0
        self.left_pos = 0.0
        self.right_pos = 0.0
        self.last_time = self.get_clock().now()

        self.tf_broadcaster = TransformBroadcaster(self)

        # STM32에서 오는 raw 데이터 구독
        self.joint_state_sub = self.create_subscription(
            JointState,
            '/joint_states',
            self.joint_state_callback,
            10)

        # robot_state_publisher용으로 정제된 joint_states 퍼블리시
        self.joint_state_pub = self.create_publisher(
            JointState, '/joint_states/filtered', 10)

        self.odom_pub = self.create_publisher(Odometry, 'odom', 10)
        self.timer = self.create_timer(0.05, self.timer_callback)
        self.get_logger().info('OdometryNode 시작')

    def euler_to_quaternion(self, roll, pitch, yaw):
        qx = sin(roll/2)*cos(pitch/2)*cos(yaw/2) - cos(roll/2)*sin(pitch/2)*sin(yaw/2)
        qy = cos(roll/2)*sin(pitch/2)*cos(yaw/2) + sin(roll/2)*cos(pitch/2)*sin(yaw/2)
        qz = cos(roll/2)*cos(pitch/2)*sin(yaw/2) - sin(roll/2)*sin(pitch/2)*cos(yaw/2)
        qw = cos(roll/2)*cos(pitch/2)*cos(yaw/2) + sin(roll/2)*sin(pitch/2)*sin(yaw/2)
        return qx, qy, qz, qw

    def joint_state_callback(self, msg: JointState):
        """STM32 raw joint_state → 내부 상태 업데이트 후 /joint_states/filtered 재발행"""
        for i, name in enumerate(msg.name):
            vel = msg.velocity[i] if i < len(msg.velocity) else 0.0
            pos = msg.position[i] if i < len(msg.position) else 0.0

            if name == 'left_wheel_joint':
                self.left_vel = -vel if self.invert_left else vel
                self.left_pos = math.fmod(-pos if self.invert_left else pos, 2*math.pi)
            elif name == 'right_wheel_joint':
                self.right_vel = -vel if self.invert_right else vel
                self.right_pos = math.fmod(-pos if self.invert_right else pos, 2*math.pi)

        # robot_state_publisher가 바퀴 TF를 만들 수 있도록 /joint_states/filtered 발행
        new_msg = JointState()
        new_msg.header.stamp = self.get_clock().now().to_msg()
        new_msg.name = ['left_wheel_joint', 'right_wheel_joint']
        new_msg.position = [self.left_pos, self.right_pos]
        new_msg.velocity = [self.left_vel, self.right_vel]
        self.joint_state_pub.publish(new_msg)

    def timer_callback(self):
        current_time = self.get_clock().now()
        dt = (current_time - self.last_time).nanoseconds / 1e9
        self.last_time = current_time

        if dt == 0:
            return

        left_ms  = self.left_vel  * self.wheel_radius
        right_ms = self.right_vel * self.wheel_radius
        linear  = (right_ms + left_ms) / 2.0

        # ★ 수정: (right - left) 가 올바른 차동구동 angular 공식
        # left > right → 왼쪽이 빠름 → 오른쪽(반시계)으로 회전 → angular 양수
        angular = (right_ms - left_ms) / self.wheel_separation

        self.x     += linear * cos(self.theta) * dt
        self.y     += linear * sin(self.theta) * dt
        self.theta += angular * dt

        qx, qy, qz, qw = self.euler_to_quaternion(0, 0, self.theta)

        # ★ 수정: covariance를 작게 → SLAM이 오도메트리를 신뢰하게 됨
        # 위치(x,y,yaw)만 작게, 나머지(z,roll,pitch)는 크게
        pose_cov = [
            0.001, 0,     0,     0,     0,     0,
            0,     0.001, 0,     0,     0,     0,
            0,     0,     1e6,   0,     0,     0,
            0,     0,     0,     1e6,   0,     0,
            0,     0,     0,     0,     1e6,   0,
            0,     0,     0,     0,     0,     0.001,
        ]
        twist_cov = [
            0.001, 0,     0,     0,     0,     0,
            0,     1e6,   0,     0,     0,     0,
            0,     0,     1e6,   0,     0,     0,
            0,     0,     0,     1e6,   0,     0,
            0,     0,     0,     0,     1e6,   0,
            0,     0,     0,     0,     0,     0.001,
        ]

        # /odom 퍼블리시
        odom_msg = Odometry()
        odom_msg.header.stamp = current_time.to_msg()
        odom_msg.header.frame_id = self.odom_frame
        odom_msg.child_frame_id = self.base_footprint_frame
        odom_msg.pose.pose.position.x = self.x
        odom_msg.pose.pose.position.y = self.y
        odom_msg.pose.pose.orientation.x = qx
        odom_msg.pose.pose.orientation.y = qy
        odom_msg.pose.pose.orientation.z = qz
        odom_msg.pose.pose.orientation.w = qw
        odom_msg.twist.twist.linear.x  = linear
        odom_msg.twist.twist.angular.z = angular
        odom_msg.pose.covariance  = pose_cov
        odom_msg.twist.covariance = twist_cov
        self.odom_pub.publish(odom_msg)

        # TF: odom → base_footprint (base_link는 robot_state_publisher가 담당)
        t = TransformStamped()
        t.header.stamp = current_time.to_msg()
        t.header.frame_id = self.odom_frame
        t.child_frame_id  = self.base_footprint_frame
        t.transform.translation.x = self.x
        t.transform.translation.y = self.y
        t.transform.translation.z = 0.0
        t.transform.rotation.x = qx
        t.transform.rotation.y = qy
        t.transform.rotation.z = qz
        t.transform.rotation.w = qw
        self.tf_broadcaster.sendTransform(t)

        self.get_logger().info(
            f'odom | x:{self.x:.2f} y:{self.y:.2f} θ:{self.theta*180/pi:.1f}°',
            throttle_duration_sec=1.0)


def main(args=None):
    rclpy.init(args=args)
    node = OdometryNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()