from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator #转换接口
import rclpy

def main():
    rclpy.init()
    nav = BasicNavigator()#节点

    target_pose = PoseStamped()
    target_pose.header.frame_id="map"
    target_pose.header.stamp=nav.get_clock().now().to_msg()
    target_pose.pose.position.x=2.0
    target_pose.pose.position.y=1.0
    target_pose.pose.position.z=1.0
    nav.goToPose(target_pose)
    while not nav.isTaskComplete():
        feedback=nav.getFeedback()
        nav.get_logger().info(f'剩余距离：{feedback.distance_remaining}')
        # nav.cancelTask()
    result=nav.getResult()
    nav.get_logger().info(f'导航结果：{result}')
    # goToPose里面包含spin和shutdown
    # rclpy.spin(nav)
    # rclpy.shutdown()