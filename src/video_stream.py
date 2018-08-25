# Threaded camera support for webcam/Raspberry Pi
# Inspired by Adrian Rosebrock's posts on pyimagesearch.com:
# https://www.pyimagesearch.com/2015/12/21/increasing-webcam-fps-with-python-and-opencv/
# https://www.pyimagesearch.com/2015/12/28/increasing-raspberry-pi-fps-with-python-and-opencv/
# https://www.pyimagesearch.com/2016/01/04/unifying-picamera-and-cv2-videocapture-into-a-single-class-with-opencv/

import cv2
import datetime

from threading import Event, Thread
from abc import ABC, abstractmethod
from open_gesture import gframe

class FPS:
    '''
    Use this to approximate frames per second
    '''
    def __init__(self):
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
    '''
    Abstract base class for various camera/video stream implementations
    '''
    def __init__(self, frame=None):
        self.frame = frame
        self.kill = None
        self.stopped = True
        self.start()
        
    def start(self):
        '''
        Start reading frames in a new thread
        '''
        if not self.stopped:
            return self
        self.kill = Event()
        self.stopped = False
        Thread(target=self.update, args=()).start()
        return self
 
    def stop(self):
        '''
        Stop reading new frames
        '''
        self.stopped = True

    def read(self):
        '''
        Get the last frame read by the camera
        '''
        return gframe(self.frame)

    def release(self):
        '''
        Stop camera and release resources
        '''
        self.stop()
        self.kill.wait() # wait for thread to end before releasing camera
        self._release()

    @abstractmethod
    def update(self):
        '''
        Continuously reads in frames in another thread
        '''
        pass
    
    @abstractmethod
    def isOpened(self):
        '''
        Check if the camera is available for use
        '''
        pass

    @abstractmethod
    def _release(self):
        '''
        Release camera resources
        '''
        pass
    
class WebcamVideoStream(VideoStream):
    '''
    VideoStream implementation for webcams and usb cameras
    Also works for reading in video files, src=/path/to/file
    '''
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
    '''
    VideoStream implementation for the Raspberry Pi camera
    '''
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
