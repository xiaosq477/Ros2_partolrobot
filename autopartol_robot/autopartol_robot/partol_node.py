import rclpy
from geometry_msgs.msg import PoseStamped,Pose
from nav2_simple_commander.robot_navigator import BasicNavigator,TaskResult #转换接口
from rclpy.node import Node
from tf2_ros import TransformListener,Buffer #坐标监听器
from geometry_msgs.msg import TransformStamped #消息接口
from tf_transformations import euler_from_quaternion,quaternion_from_euler #四元数转欧拉角
import math #角度转弧度函数
from autopartol_interfaces.srv import SpeechText
from sensor_msgs.msg import Image#消息接口
from cv_bridge import CvBridge#转换图像格式
import cv2#保存图像

class PartolNode(BasicNavigator):
    def __init__(self, node_name='patrol_robot'):
        super().__init__(node_name)
        #声明相关参数
        self.buffer_=Buffer()
        self.declare_parameter('initial_point',[0.0, 0.0, 0.0])
        self.declare_parameter('target_point',[0.0, 0.0, 0.0, 1.0, 1.0, 1.57])
        self.declare_parameter('img_save_path','')
        self.initial_point=self.get_parameter('initial_point').value
        self.target_points=self.get_parameter('target_point').value
        self.img_save_path_=self.get_parameter('img_save_path').value
        self.listener_=TransformListener(self.buffer_,self)
        self.speech_client_=self.create_client(SpeechText,'speech_text')
        self.cv_bridge_=CvBridge()
        self.latest_img_=None
        self.img_sub_=self.create_subscription(Image,'/camera',self.img_callback,1)

    def img_callback(self,msg):
        self.latest_img_=msg

    def record_img(self):
        if self.latest_img_ is not None:
            pose=self.get_current_pose()
            cv_image=self.cv_bridge_.imgmsg_to_cv2(self.latest_img_)
            cv2.imwrite(
                f'{self.img_save_path_}img_{
                    pose.translation.x:3.2f}_{
                    pose.translation.y:3.2f}.png',
                cv_image
            )

    def get_pose_by_xyyaw(self,x,y,yaw):
        """return PoseStamped对象"""
        pose=PoseStamped()
        pose.header.frame_id='map'
        pose.pose.position.x=x;
        pose.pose.position.y=y;
        quat=quaternion_from_euler(0,0,yaw)
        pose.pose.orientation.x=quat[0]
        pose.pose.orientation.y=quat[1]
        pose.pose.orientation.z=quat[2]
        pose.pose.orientation.w=quat[3]
        return pose

    def init_robot_pose(self):
        """初始化位姿"""
        self.initial_point=self.get_parameter('initial_point').value
        init_pose=self.get_pose_by_xyyaw(self.initial_point[0],self.initial_point[1],self.initial_point[2])
        self.setInitialPose(init_pose)
        self.waitUntilNav2Active()

    def get_target_points(self):
        """通过参数值获取目标点集合"""
        points=[]
        self.target_points=self.get_parameter('target_point').value
        for index in range(int(len(self.target_points)/3)):
            x=self.target_points[index*3]
            y=self.target_points[index*3+1]
            yaw=self.target_points[index*3+2]
            points.append([x,y,yaw])
            self.get_logger().info(f"获取到目标点{index}->{x},{y},{yaw}")
        return points

    def nav_to_pose(self,target_point):
        """导航到目标点"""
        self.goToPose(target_point)
        while not self.isTaskComplete():
            feedback=self.getFeedback()
            self.get_logger().info(f'剩余距离：{feedback.distance_remaining}')
            # nav.cancelTask()
            rclpy.spin_once(self)
        result=self.getResult()
        self.get_logger().info(f'导航结果：{result}')

    def get_current_pose(self):
        """获取机器人当前位姿"""
        while rclpy.ok():
            try:
                result=self.buffer_.lookup_transform('map','base_link',
                        rclpy.time.Time(seconds=0),rclpy.time.Duration(seconds=1.0))
                #查询最新时间（0秒时刻），超时时间为1秒的两坐标关系
                transform=result.transform
                self.get_logger().info(f'平移{transform.translation}')
                return transform
            except Exception as e:
                self.get_logger().warn(f'获取坐标变换失败，原因：{str(e)}')

    def speech_text(self,text):
        """调用合成语音"""
        while not self.speech_client_.wait_for_service(timeout_sec=1):
            self.get_logger().info('语音合成服务未上线，正在等待...')
        request=SpeechText.Request()
        request.text=text
        future=self.speech_client_.call_async(request)
        rclpy.spin_until_future_complete(self,future)
        if future.result() is not None:
            response=future.result()
            if response.result==True:
                self.get_logger().info(f'语音合成功{text}')
            else:
                self.get_logger().warn(f'语音合失败{text}')
        else:
                self.get_logger().warn(f'语音合服务相应失败{text}')


def main():
    rclpy.init()
    partol = PartolNode()#节点
    # rclpy.spin(partol)
    partol.speech_text('正在初始化位置')
    partol.init_robot_pose()
    partol.speech_text('初始化位置完成')
    while rclpy.ok():
        points=partol.get_target_points()
        for point in points:
            x,y,yaw=point[0],point[1],point[2]
            target_pose=partol.get_pose_by_xyyaw(x,y,yaw)
            partol.speech_text(f'正在准备前往{x},{y}目标点')
            partol.nav_to_pose(target_pose)
            partol.speech_text(f'已经到达{x},{y}目标点，正在记录图像')
            partol.record_img()
            partol.speech_text(f'图像记录完成')
    rclpy.shutdown()