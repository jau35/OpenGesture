# Threaded camera support for webcam/Raspberry Pi
# Inspired by Adrian Rosebrock's posts on pyimagesearch.com:
# https://www.pyimagesearch.com/2015/12/21/increasing-webcam-fps-with-python-and-opencv/
# https://www.pyimagesearch.com/2015/12/28/increasing-raspberry-pi-fps-with-python-and-opencv/
# https://www.pyimagesearch.com/2016/01/04/unifying-picamera-and-cv2-videocapture-into-a-single-class-with-opencv/

import cv2
import datetime

from threading import Event, Thread
from abc import ABC, abstractmethod

class FPS:
    def __init__(self):
        # maintain start time, end time, and number of frames
        self._start = None
        self._end = None
        self._numFrames = 0
 
    def start(self):
        self._start = datetime.datetime.now()
        return self
 
    def stop(self):
        self._end = datetime.datetime.now()
 
    def update(self):
        self._numFrames += 1
 
    def elapsed(self):
        return (self._end - self._start).total_seconds()
 
    def fps(self):
        return self._numFrames / self.elapsed()

class VideoStream(ABC):
    def __init__(self, frame=None):
        self.frame = frame
        self.kill = None
        self.stopped = True
        self.start()
        
    def start(self):
        if not self.stopped:
            return self
        self.kill = Event()
        self.stopped = False
        Thread(target=self.update, args=()).start()
        return self
 
    def stop(self):
        self.stopped = True

    def read(self):
        return self.frame

    def release(self):
        self.stop()
        self.kill.wait() # wait for thread to end before releasing camera
        self._release()

    @abstractmethod
    def update(self):
        pass
    
    @abstractmethod
    def isOpened(self):
        pass

    @abstractmethod
    def _release(self):
        pass
    
class WebcamVideoStream(VideoStream):
    def __init__(self, src=0):
        self.stream = cv2.VideoCapture(src)
        self.stream.set(10,200)
        self.grabbed, self.frame = self.stream.read()
        super().__init__(self.frame)
    
    def update(self):
        while True:
            if self.stopped:
                self.kill.set() # signal thread is ending
                return
            self.grabbed, self.frame = self.stream.read()

    def isOpened(self):
        return self.stream.isOpened()

    def _release(self):
        self.stream.release()
 

class PiVideoStream(VideoStream):
    def __init__(self, resolution=(320, 240), framerate=32):
        from picamera.array import PiRGBArray
        from picamera import PiCamera

        self.camera = PiCamera()
        self.camera.resolution = resolution
        self.camera.framerate = framerate
        self.rawCapture = PiRGBArray(self.camera, size=resolution)
        self.stream = self.camera.capture_continuous(self.rawCapture,
            format="bgr", use_video_port=True)
        super().__init__()
 
    def update(self):
        for f in self.stream:
            if self.stopped:
                self.kill.set() # signal thread is ending
                return
            self.frame = f.array
            self.rawCapture.truncate(0)

    def isOpened(self):
        try:
            self.camera._check_camera_open()
            return True
        except:
            return False

    def _release(self):
        self.stream.close()
        self.rawCapture.close()
        self.camera.close()

class CameraWrapper:
    def __init__(self, src=0, usePiCamera=False, resolution=(320,240), framerate=32):
        if usePiCamera:
            self.videostream = PiVideoStream(resolution=resolution, framerate=framerate)
        else:
            self.videostream = WebcamVideoStream(src=src)
    
    def isOpened(self):
        return self.videostream.isOpened()

    def release(self):
        self.videostream.release()

    def start(self):
        return self.videostream.start()
 
    def update(self):
        self.videostream.update()
 
    def read(self):
        return self.videostream.read()
 
    def stop(self):
        self.videostream.stop()
