import rclpy
from rclpy.node import Node
from tf2_ros import TransformListener,Buffer #坐标监听器
from geometry_msgs.msg import TransformStamped #消息接口
from tf_transformations import euler_from_quaternion #四元数转欧拉角
import math #角度转弧度函数

class TFBroadcaster(Node):
    def __init__(self):
        super().__init__('static_tf_broadcaster')
        self.buffer_=Buffer()
        self.broadcaster_=TransformListener(self.buffer_,self)
        self.timer_=self.create_timer(0.01,self.get_transform)

    def get_transform(self):
        """"实时查询坐标关系"""
        try:
            result=self.buffer_.lookup_transform('map','base_link',
                    rclpy.time.Time(seconds=0),rclpy.time.Duration(seconds=1.0))
            #查询最新时间（0秒时刻），超时时间为1秒的两坐标关系
            transform=result.transform
            self.get_logger().info(f'平移{transform.translation}')
            self.get_logger().info(f'旋转{transform.rotation}')
            euler=euler_from_quaternion([transform.rotation.x,
                                        transform.rotation.y,
                                        transform.rotation.z,
                                        transform.rotation.w])
            self.get_logger().info(f'欧拉{transform.translation}')
        except Exception as e:
            self.get_logger().warn(f'获取坐标变换失败，原因：{str(e)}')

        #坐标关系发布出去
        #self.broadcaster_.sendTransform(transform)
        #self.get_logger().info(f'静态坐标发布：{transform}')

def main():
    rclpy.init()
    node=TFBroadcaster()
    rclpy.spin(node)
    rclpy.shutdown()