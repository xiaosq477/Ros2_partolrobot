from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator #转换接口
import rclpy

def main():
    rclpy.init()
    nav = BasicNavigator()#节点
    target_poses=[]
    target_pose = PoseStamped()
    target_pose.header.frame_id="map"
    target_pose.header.stamp=nav.get_clock().now().to_msg()
    target_pose.pose.position.x=2.0
    target_pose.pose.position.y=1.0
    target_pose.pose.position.z=1.0
    target_poses.append(target_pose)
    target_pose1 = PoseStamped()
    target_pose1.header.frame_id="map"
    target_pose1.header.stamp=nav.get_clock().now().to_msg()
    target_pose1.pose.position.x=0.0
    target_pose1.pose.position.y=3.0
    target_pose1.pose.position.z=1.0
    target_poses.append(target_pose1)
    target_pose2 = PoseStamped()
    target_pose2.header.frame_id="map"
    target_pose2.header.stamp=nav.get_clock().now().to_msg()
    target_pose2.pose.position.x=0.0
    target_pose2.pose.position.y=0.0
    target_pose2.pose.position.z=1.0
    target_poses.append(target_pose2)
    nav.followWaypoints(target_poses)
    while not nav.isTaskComplete():
        feedback=nav.getFeedback()
        nav.get_logger().info(f'路点编号{feedback.current_waypoint}')
        # nav.cancelTask()
    result=nav.getResult()
    nav.get_logger().info(f'导航结果：{result}')
    # goToPose里面包含spin和shutdown
    # rclpy.spin(nav)
    # rclpy.shutdown()