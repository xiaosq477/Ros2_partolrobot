import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import math
import time
import tf2_ros

class ClosedLoopExplorer(Node):
    def __init__(self):
        super().__init__('closed_loop_explorer')
        self.publisher_ = self.create_publisher(Twist, '/cmd_vel', 10)
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)
        
    def get_pose(self):
        try:
            # 不等待超时，直接拿最新数据
            t = self.tf_buffer.lookup_transform('odom', 'base_link', rclpy.time.Time())
            x = t.transform.translation.x
            y = t.transform.translation.y
            q = t.transform.rotation
            siny_cosp = 2 * (q.w * q.z + q.x * q.y)
            cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
            yaw = math.atan2(siny_cosp, cosy_cosp)
            return x, y, yaw
        except Exception:
            return None, None, None

    def go_to(self, target_x, target_y):
        self.get_logger().info(f"==> 目标点: ({target_x:.1f}, {target_y:.1f})")
        msg = Twist()
        
        while rclpy.ok():
            x, y, yaw = self.get_pose()
            
            if x is None:
                self.get_logger().info("等待 TF 数据...", throttle_duration_sec=1.0)
                time.sleep(0.1)
                continue
            
            print(f"当前坐标: x={x:.2f}, y={y:.2f}, yaw={yaw:.2f}", end='\r')
                
            dx = target_x - x
            dy = target_y - y
            distance = math.sqrt(dx**2 + dy**2)
            
            if distance < 0.1:  # 到达目标点（误差10厘米内）
                self.stop()
                break
                
            target_yaw = math.atan2(dy, dx)
            yaw_error = target_yaw - yaw
            while yaw_error > math.pi: yaw_error -= 2 * math.pi
            while yaw_error < -math.pi: yaw_error += 2 * math.pi
            
            if abs(yaw_error) > 0.5:
                msg.linear.x = 0.0
                msg.angular.z = 0.5 if yaw_error > 0 else -0.5
            else:
                msg.linear.x = 0.15
                msg.angular.z = yaw_error * 1.0
                
            self.publisher_.publish(msg)
            time.sleep(0.05)

    def stop(self):
        msg = Twist()
        self.publisher_.publish(msg)
        time.sleep(0.5)

    def run_path(self):
        self.stop()
        print("等待 TF 数据...")
        
        # 规划一段简单的路线：沿着 y=0 走，避开障碍物
        waypoints = [
            (1.5, 0.0),   # 先往前开
            (-1.5, 0.0),  # 再往回开
            (0.0, 0.0)    # 回到原点
        ]
        
        for tx, ty in waypoints:
            self.go_to(tx, ty)
            
        print("\n建图路线完成！")

def main(args=None):
    rclpy.init(args=args)
    explorer = ClosedLoopExplorer()
    explorer.run_path()
    explorer.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()