import cv2
import numpy
import copy
import math

class gframe:
    def __init__(self, arr):
        self.frame = arr
    
    def get(self):
        return self.frame

    def blur(self):
        self.frame = cv2.bilateralFilter(self.frame, 9, 75, 75)

    def flip(self, dir=1):
        self.frame = cv2.flip(self.frame, dir)

    def show(self, title='frame', wait=1):
        cv2.namedWindow(title)
        cv2.imshow(title, self.frame)
        return cv2.waitKey(wait)
        
class gframe_sequence:
    def __init__(self, seq=[]):
        self.sequence = seq
        
    def __getitem__(self, index):
        return self.sequence[index]

    def __len__(self):
        return len(self.sequence)
    
    def append_frame(self, frame):
        self.sequence.append(frame)

    def playback(self, wait=1):
        for frame in self.sequence:
            k = frame.show(title="playback", wait=wait)
            if(k == 27):
                break

def capture_sequence(camera, num_frames, show_frames=False):
    sequence = gframe_sequence()
    
    for i in range(0, num_frames):
        ret, arr = camera.read()
        f = gframe(arr)
        f.flip()
        if(show_frames):
            f.show("capturing sequence")
        sequence.append_frame(f)

    if(show_frames):
        cv2.destroyWindow("capturing sequence")

    return sequence


