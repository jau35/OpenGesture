import sys
import cv2
import numpy as np

from tegra_cam import open_cam_onboard

# def open_onboard_cam():
# 	gst_str = "nvcamerasrc ! vide/x-raw(memory:NVMM), width=(int)1280, height=(int)720,\
# 	format=(string)I420, framerate=(fraction)30/1 ! nvvidconv flip-method=0 ! video/x-raw,\
# 	format=(string)BGRx ! videoconvert ! video/x-raw, format=(string)BGR ! appsink"
# 	cap = cv2.VideoCapture(gst_str)
# 	return cap

def read_cam(cap):
	if not cap.isOpened():
		sys.exit("failed to open camera")
	
	else:
		windowName = "Face Detection"
		cv2.namedWindow(windowName, cv2.WINDOW_NORMAL)
		cv2.resizeWindow(windowName, 1280, 720)
		cv2.moveWindow(windowName, 0, 0)
		cv2.setWindowTitle(windowName, "Face Detection")

		showHelp = True
		font = cv2.FONT_HERSHEY_PLAIN
		helpText = "Face Detection"

		while True:
			if cv2.getWindowProperty(windowName, 0) < 0:
				break
			ret_val, frame = cap.read()
			gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

			frameRs = cv2.resize(frame, (640, 360))
			grayRs = cv2.resize(gray_frame, (640, 360))
			cascadeLocation = "/usr/local/share/OpenCV/haarcascades/"
			faceCascadeFile = "haarcascade_frontalface_default.xml"
			faceCascade = cv2.CascadeClassifier(cascadeLocation + faceCascadeFile)
			faces = faceCascade.detectMultiScale(grayRs, 1.3, 5)
			for (x, y, w, h) in faces:
				grayRs = cv2.rectangle(grayRs, (x, y), (x+w, y+h), (255, 0, 0), 2)

			displayBuf = grayRs

			if showHelp == True:
				cv2.putText(displayBuf, helpText, (11, 20), font, 1.0, (32, 32, 32), 4,\
				cv2.LINE_AA)
				cv2.putText(displayBuf, helpText, (10, 20), font, 1.0, (32, 32, 32), 1,\
				cv2.LINE_AA)

			cv2.imshow(windowName, displayBuf)
			key = cv2.waitKey(10)
			if key == 27: # ESC key = quit
				cv2.destroyAllWindows()

			else:
				print("camera open failed")

if __name__ =='__main__':
	cap = open_cam_onboard(1280, 720)
	read_cam(cap)
	
