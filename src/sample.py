import cv2, numpy
from open_gesture import gframe, gframe_sequence, capture_sequence
from time import sleep

showDuringCapture = True

def countdown(n):
    print("capturing sequence in...")
    sleep(1)
    print(n)
    for i in range(1, n):
        sleep(1)
        print(n-i)

    sleep(1)

camera = cv2.VideoCapture(0)
camera.set(10,200)

countdown(3)

if camera.isOpened():
    sequence = capture_sequence(camera, 100, showDuringCapture)
    sequence.playback(100)
    cv2.destroyAllWindows()

camera.release()