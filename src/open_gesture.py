import cv2
import numpy
import copy
import math

def capture_background(camera, bg_threshold, x_begin=0, x_end=1, y_begin=0, y_end=1):
    '''
    Capture a background image and initialize an OpenCV background model
    @param camera - VideoStream object
    @param bg_threshold - background threshold to initialize background model
    @return - background model
    '''
    bg_model = cv2.createBackgroundSubtractorMOG2(0, bg_threshold)
    
    # first frame
    f = camera.read()
    f.flip()
    f.crop(x_begin, x_end, 
           y_begin, y_end)
    bg_model.apply(f.get(), learningRate=0)
    
    return bg_model

class gframe:
    '''
    Supports various operations on video frames
    '''
    gaussian_blur_value = 41
    binary_threshold = 60
    learning_rate = 0

    def __init__(self, arr):
        self.frame = arr
    
    def get(self):
        return self.frame

    def flip(self, dir=1):
        self.frame = cv2.flip(self.frame, dir)
    
    def gray(self):
        self.frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)

    def blur(self):
        self.frame = cv2.GaussianBlur(self.frame, (self.gaussian_blur_value, self.gaussian_blur_value), 0)

    def threshold(self):
        self.frame = cv2.threshold(self.frame, self.binary_threshold, 255, cv2.THRESH_BINARY)[1]

    def get_contours(self):
        '''Returns list of contours, sorted by area (largest to smallest)'''
        cpy = copy.deepcopy(self.frame)
        _,contours,hierarchy = cv2.findContours(cpy, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        return sorted(contours, key=lambda c: cv2.contourArea(c), reverse=True)

    def remove_bg(self, bg_model):
        fgmask = bg_model.apply(self.frame,learningRate=self.learning_rate)
        kernel = numpy.ones((3, 3), numpy.uint8)
        fgmask = cv2.erode(fgmask, kernel, iterations=1)
        self.frame = cv2.bitwise_and(self.frame, self.frame, mask=fgmask)
    
    def crop(self, x_begin=0, x_end=1, y_begin=0, y_end=1):
        self.frame = self.frame[int(y_begin * self.frame.shape[0]):int(y_end * self.frame.shape[0]), 
                         int(x_begin * self.frame.shape[1]):int(x_end * self.frame.shape[1])]
    
    def show(self, title='frame', wait=1):
        cv2.namedWindow(title)
        cv2.imshow(title, self.frame)
        return cv2.waitKey(wait)
        
class gframe_sequence:
    '''
    Capture and playback a sequence of gframe objects
    '''
    def __init__(self, seq=[]):
        self.sequence = seq
        
    def __getitem__(self, index):
        return self.sequence[index]

    def __len__(self):
        return len(self.sequence)
    
    def append_frame(self, frame):
        self.sequence.append(frame)
    
    def capture(self, camera, num_frames, show_frames=False):
        ''' 
        Capture a sequence of frames from the camera
        @param camera - VideoStream object
        @param num_frames - number of frames to capture
        @param show_frames - display video stream as the frames are captured
        '''
        for i in range(0, num_frames):
            f = camera.read()
            f.flip()
            if(show_frames):
                f.show("capturing sequence")
            self.append_frame(f)

        if(show_frames):
            cv2.destroyWindow("capturing sequence")

    def playback(self, wait=1):
        '''
        Playback the sequence
        @param wait - ms delay between each frame (> 0)
        '''
        for frame in self.sequence:
            k = frame.show(title="playback", wait=wait)
            if(k == 27): # ESC
                break
