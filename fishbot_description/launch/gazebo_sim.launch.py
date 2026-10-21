import launch
import launch_ros
from launch_ros.parameter_descriptions import ParameterValue
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    urdf_package_path = get_package_share_directory('fishbot_description')

    default_xacro_path = os.path.join(
        urdf_package_path, 'urdf', 'fishbot', 'fishbot.urdf.xacro'
    )

    default_gazebo_world_config_path = '/home/junf/chapt7/chapt7_ws/src/fishbot_description/world/room.world'

    action_declare_arg_mode_path = launch.actions.DeclareLaunchArgument(
        name='model',
        default_value=str(default_xacro_path),
        description='加载的模型文件路径'
    )

    substitutions_command_result = launch.substitutions.Command([
        'xacro ',
        launch.substitutions.LaunchConfiguration('model')
    ])
    robot_description_value = ParameterValue(
        substitutions_command_result, value_type=str
    )

    action_robot_state_publisher = launch_ros.actions.Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': robot_description_value,
                     'use_sim_time': True}]
    )

    action_convert_to_sdf = launch.actions.ExecuteProcess(
        cmd=[
            'bash', '-c',
            'xacro ' + default_xacro_path + ' > /tmp/fishbot.urdf && '
            'gz sdf -p /tmp/fishbot.urdf > /tmp/fishbot.sdf'
        ],
        output='screen'
    )

    gazebo_launch_path = os.path.join(
        get_package_share_directory('ros_gz_sim'),
        'launch',
        'gz_sim.launch.py'
    )
    action_launch_gazebo = launch.actions.IncludeLaunchDescription(
        launch.launch_description_sources.PythonLaunchDescriptionSource(
            gazebo_launch_path
        ),
        launch_arguments=[
            ('gz_args', f'-r -v 4 {default_gazebo_world_config_path}')
        ]
    )

    action_spawn_entity = launch_ros.actions.Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-world', 'default',
            '-file', '/tmp/fishbot.sdf',
            '-name', 'fishbot',
            '-x', '0.0', '-y', '0.0', '-z', '0.1',
        ],
        output='screen'
    )

    action_spawn_after_delay = launch.actions.TimerAction(
        period=8.0,
        actions=[action_spawn_entity]
    )

    # bridge 里删掉 /joint_states，避免和 broadcaster QoS 冲突
    action_bridge = launch_ros.actions.Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/world/default/clock@rosgraph_msgs/msg/Clock@gz.msgs.Clock',
            '/cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist',
            '/odom@nav_msgs/msg/Odometry@gz.msgs.Odometry',
            '/tf@tf2_msgs/msg/TFMessage@gz.msgs.Pose_V',
            # '/clock@rosgraph_msgs/msg/Clock@gz.msgs.Clock',
            '/scan@sensor_msgs/msg/LaserScan@gz.msgs.LaserScan',
            '/imu@sensor_msgs/msg/Imu@gz.msgs.IMU',
            '/camera@sensor_msgs/msg/Image@gz.msgs.Image',
            '/camera/points@sensor_msgs/msg/PointCloud2@gz.msgs.PointCloudPacked',
        ],
        remappings=[
            ('/world/default/clock', '/clock'),
        ],
        output='screen'
    )

    # action_clock_relay = launch_ros.actions.Node(
    #     package='topic_tools',
    #     executable='relay',
    #     arguments=['/world/default/clock', '/clock'],
    #     parameters=[{'use_sim_time': False}],
    #     output='screen'
    # )

    action_spawn_jsb = launch_ros.actions.Node(
        package='controller_manager',
        executable='spawner',
        arguments=['fishbot_joint_state_broadcaster',
                   '--controller-manager-timeout', '60'],
        output='screen'
    )

    action_diff_drive_controller = launch_ros.actions.Node(
        package='controller_manager',
        executable='spawner',
        arguments=['fishbot_diff_drive_controller',
                   '--controller-manager-timeout', '60'],
        output='screen'
    )

    action_spawn_controllers_after_delay = launch.actions.TimerAction(
        period=20.0,
        actions=[action_spawn_jsb, action_diff_drive_controller]
    )

    action_twist_to_twist_stamped = launch.actions.ExecuteProcess(
        cmd=[
            'python3',
            os.path.join(urdf_package_path, 'scripts', 'twist_to_twist_stamped.py')
        ],
        output='screen'
    )

    return launch.LaunchDescription([
        action_declare_arg_mode_path,
        action_convert_to_sdf,
        action_robot_state_publisher,
        action_launch_gazebo,
        action_bridge,
        # action_clock_relay,
        action_twist_to_twist_stamped,
        action_spawn_after_delay,
        action_spawn_controllers_after_delay,
    ])