import cv2, numpy, argparse
from open_gesture import gframe_sequence, capture_background
from video_stream import WebcamVideoStream, PiVideoStream
from time import sleep
from functools import partial

num_frames = 250

bg_threshold = 50
show_during_capture = False

# bounding box parameters (specify the range of the frame to consider)
# e.g. x: 0.5 -> 1 is the right half of the frame
#      y: 0 -> 0.8 is the top 80% of the frame
begin_x_range=0.5
end_x_range=1
begin_y_range=0.2
end_y_range=1

def countdown(n, msg):
    print(msg)
    sleep(1)
    print(n)
    for i in range(1, n):
        sleep(1)
        print(n-i)
    sleep(1)

def preprocessFrame(frame):
    frame.flip()
    frame.crop(x_begin=begin_x_range, x_end=end_x_range, 
               y_begin=begin_y_range, y_end=end_y_range)

def processFrame(bg_model, frame):
    preprocessFrame(frame)
    frame.remove_bg(bg_model)
    frame.gray()
    frame.blur()
    frame.threshold()

    contours = frame.get_contours()
    if(len(contours) > 0):
        hull = cv2.convexHull(contours[0])
        rgb = cv2.cvtColor(frame.frame, cv2.COLOR_GRAY2RGB)
        frame.frame = numpy.zeros(rgb.shape, numpy.uint8)
        cv2.drawContours(frame.frame, contours, -1, (0, 255, 0), 2)
        cv2.drawContours(frame.frame, [hull], -1, (0, 0, 255), 3)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-pi", "--RaspberryPi", action="store_true", help="Use raspberry pi camera interface")
    args = parser.parse_args()

    if args.RaspberryPi:
        camera = PiVideoStream()
    else:
        camera = WebcamVideoStream()

    if camera.isOpened():
        countdown(3, "capturing background in...")
        bg_model = capture_background(camera, bg_threshold, preprocess_cb=preprocessFrame)

        countdown(3, "capturing sequence in...")
        sequence = gframe_sequence()
        sequence.capture(camera, num_frames, preprocess_cb=partial(processFrame, bg_model), show_frames=show_during_capture)
        
        sequence.playback(1)
        cv2.destroyAllWindows()

    camera.release()

if __name__ == '__main__':
    main()