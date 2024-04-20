import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.core.window import Window
from kivy.utils import platform
from kivy.uix.camera import Camera
import cv2
import serial
import math

kivy.require('1.11.1')


class FaceFollowingApp(App):

    def build(self):
        self.request_permissions()
        self.arduino = None
        self.bluetooth = None
        self.connect_to_bluetooth()
        layout = BoxLayout(orientation='vertical')
        self.camera = Camera(play=True, resolution=(640, 480), index=0)  # Set index to 0 for back camera
        layout.add_widget(self.camera)
        Clock.schedule_interval(self.update, 1.0 / 30.0)  # Update at 30fps
        return layout

    def request_permissions(self):
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.CAMERA, Permission.BLUETOOTH,
                                 Permission.BLUETOOTH_ADMIN])

    def connect_to_bluetooth(self):
        if platform == 'android':
            import android
            import android.bluetooth as bt
            paired_devices = bt.get_paired_devices()
            if paired_devices:
                for device in paired_devices:
                    if device[0] == "HC-05":  # Replace with your Arduino's Bluetooth name
                        self.bluetooth = bt.BluetoothSPP()
                        self.bluetooth.connect(device[0])

    def update(self, dt):
        if self.camera.texture:
            frame = self.camera.texture
            frame.flip_horizontal()  # Flip the frame horizontally for correct display
            frame_data = frame.pixels
            gray = cv2.cvtColor(frame_data, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

            for (x, y, w, h) in faces:
                cv2.rectangle(frame_data, (x, y), (x + w, y + h), (0, 255, 0), 2)
                face_center_x = x + w // 2
                face_center_y = y + h // 2
                frame_center_x = frame.width // 2
                frame_center_y = frame.height // 2
                distance = math.sqrt((frame_center_x - face_center_x) ** 2 + (frame_center_y - face_center_y) ** 2)

                if distance <= 40:
                    self.send_command('B')  # Move backward
                elif distance > 80:
                    self.send_command('F')  # Move forward
                else:
                    if face_center_x < frame_center_x - 50:
                        self.send_command('R')
                    elif face_center_x > frame_center_x + 50:
                        self.send_command('L')
                    else:
                        self.send_command('S')  # Stop

            buf = cv2.flip(frame_data, 0).tostring()
            texture = Texture.create(size=(frame.width, frame.height), colorfmt='bgr')
            texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
            self.camera.texture = texture

    def send_command(self, command):
        if self.bluetooth:
            self.bluetooth.send(command)


if __name__ == '__main__':
    FaceFollowingApp().run()
