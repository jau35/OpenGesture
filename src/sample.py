import cv2, numpy
from open_gesture import gframe, gframe_sequence, capture_sequence, capture_background
from time import sleep

num_frames = 50

bg_threshold = 50
show_during_capture = False

# bounding box parameters (specify the range of the frame to consider)
# e.g. x: 0.5 -> 1 is the right half of the frame
#      y: 0 -> 0.8 is the top 80% of the frame
begin_x_range=0.5
end_x_range=1
begin_y_range=0.1
end_y_range=0.9

def countdown(n, msg):
    print(msg)
    sleep(1)
    print(n)
    for i in range(1, n):
        sleep(1)
        print(n-i)
    sleep(1)

camera = cv2.VideoCapture(0)
camera.set(10,200)

if camera.isOpened():
    countdown(3, "capturing background in...")
    bg_model = capture_background(camera, bg_threshold,
                                  x_begin=begin_x_range, x_end=end_x_range, 
                                  y_begin=begin_y_range, y_end=end_y_range)

    countdown(3, "capturing sequence in...")
    sequence = capture_sequence(camera, num_frames, show_during_capture)
    
    for frame in sequence:
        frame.crop(x_begin=begin_x_range, x_end=end_x_range, 
                   y_begin=begin_y_range, y_end=end_y_range)
        frame.remove_bg(bg_model)
        frame.gray()
        frame.blur()
        frame.threshold()
        
        contours = frame.get_contours()
        if(len(contours) > 0):
            hull = cv2.convexHull(contours[0])
            frame.frame = numpy.zeros(frame.frame.shape, numpy.uint8)
            cv2.drawContours(frame.frame, contours, 0, (255, 255, 255), 0)
            cv2.drawContours(frame.frame, [hull], 0, (255, 255, 255), 0)

    sequence.playback(100)
    cv2.destroyAllWindows()

camera.release()