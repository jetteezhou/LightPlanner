import pyrealsense2 as rs
import numpy as np
import cv2
import threading


class RealSenseD435Viewer:
    def __init__(self, serial_number="836612071991", video_filename=None):
        # 创建RealSense管道
        self.pipeline = rs.pipeline()
        # 创建配置
        self.config = rs.config()
        # self.config.enable_device(serial_number)
        # 配置深度和颜色流
        self.config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
        self.config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
        # 启动流
        self.pipeline.start(self.config)
        # 创建对齐对象，以颜色流为基准对齐
        self.align = rs.align(rs.stream.color)
        # 初始化帧数据
        self.aligned_depth_frame = None
        self.color_frame = None
        self.intrinsics = None
        self.depth_intrin = None

        # 用于保存最新的图像数据
        self.color_image = None
        self.depth_image = None

        # 线程控制
        self.running = False
        self.thread = None
        self.lock = threading.Lock()

        # 初始化视频写入器
        self.video_writer = None
        self.video_filename = video_filename
        self.fps = 30  # 视频帧率
        self.frame_size = (640, 480)  # 视频的尺寸

    def get_frames(self):
        # 等待一对同步的帧：深度和颜色
        frames = self.pipeline.wait_for_frames()
        # 将深度帧对齐到颜色帧
        aligned_frames = self.align.process(frames)
        # 获取对齐后的帧
        self.aligned_depth_frame = aligned_frames.get_depth_frame()
        self.color_frame = aligned_frames.get_color_frame()
        if not self.aligned_depth_frame or not self.color_frame:
            return False

        # 获取相机内参
        self.intrinsics = self.color_frame.profile.as_video_stream_profile().intrinsics
        self.depth_intrin = self.aligned_depth_frame.profile.as_video_stream_profile().intrinsics
        return True

    def get_images(self):
        # 将帧数据转换为numpy数组
        depth_image = np.asanyarray(self.aligned_depth_frame.get_data())
        color_image = np.asanyarray(self.color_frame.get_data())
        return color_image, depth_image

    def update_frames(self):
        """
        不断获取新的帧数据并保存
        """
        while self.running:
            if self.get_frames():
                with self.lock:
                    # 获取颜色图和深度图
                    self.color_image, self.depth_image = self.get_images()
                    # 写入颜色图像到视频
                    if self.video_filename is not None:
                        self.video_writer.write(self.color_image)
            else:
                print("未获取到帧数据")
                continue

    def start(self):
        """
        启动图像获取和显示线程
        """
        self.running = True
        # 启动帧更新线程
        self.thread = threading.Thread(target=self.update_frames)
        self.thread.start()
        if self.video_filename is not None:
            # 初始化视频写入器
            fourcc = cv2.VideoWriter_fourcc(*'XVID')  # 使用XVID编码
            self.video_writer = cv2.VideoWriter(self.video_filename, fourcc, self.fps, self.frame_size)

    def stop(self):
        """
        停止线程和释放资源
        """
        self.running = False
        self.thread.join()
        self.pipeline.stop()
        if self.video_writer:
            self.video_writer.release()  # 释放视频写入器
        cv2.destroyAllWindows()

    def show_images(self):
        """
        在单独的线程中显示图像
        """
        while self.running:
            with self.lock:
                if self.color_image is not None and self.depth_image is not None:
                    # 对深度图进行颜色映射，方便可视化
                    depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(self.depth_image, alpha=0.03), cv2.COLORMAP_JET)
                    # 水平拼接两张图像
                    images = np.hstack((self.color_image, depth_colormap))
                    # 显示图像
                    cv2.namedWindow('Aligned Images', cv2.WINDOW_AUTOSIZE)
                    cv2.imshow('Aligned Images', images)

                    cv2.waitKey(1)
        cv2.destroyAllWindows()

    def get_current_data(self, x, y):
        """
        获取当前对齐后的颜色图、深度图和相机内参
        """
        with self.lock:
            dis = self.aligned_depth_frame.get_distance(x, y)
            point = rs.rs2_deproject_pixel_to_point(self.intrinsics, [x, y], dis)
            return cv2.cvtColor(self.color_image.copy(), cv2.COLOR_BGR2RGB) if self.color_image is not None else None, \
                    self.depth_image.copy() if self.depth_image is not None else None, \
                    point, \
                    self.intrinsics

    def run(self):
        """
        启动获取帧的线程和显示图像的线程
        """
        self.start()
        try:
            # 在主线程中运行显示图像的函数
            # self.show_images()
            pass
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()


# 使用示例
if __name__ == '__main__':
    viewer = RealSenseD435Viewer()
    # 启动线程
    viewer.start()

    try:
        # 在主线程中，可以随时调用get_current_data获取数据
        while True:
            number = input("number: ")
            color_image, depth_image, point, intrinsics = viewer.get_current_data(320, 240)  # 使用中心点的坐标
            # cv2.cvtColor(color_image, cv2.COLOR_RGB2BGR)
            cv2.imwrite("UR3_rgb_{}.jpg".format(number), color_image[:,:,::-1])
            cv2.imwrite("UR3_depth_{}.png".format(number), depth_image)
            threading.Event().wait(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        viewer.stop()
