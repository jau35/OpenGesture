import sys
import cv2


WINDOW_NAME = 'CameraDemo'


def open_cam_onboard(width, height):
	# On versions of L4T prior to 28.1, add 'flip-method=2' into gst_str
	gst_str = ('nvcamerasrc ! '
			   'video/x-raw(memory:NVMM), '
			   'width=(int)2592, height=(int)1458, '
			   'format=(string)I420, framerate=(fraction)30/1 ! '
			   'nvvidconv ! '
			   'video/x-raw, width=(int){}, height=(int){}, '
			   'format=(string)BGRx ! '
			   'videoconvert ! appsink').format(width, height)
	return cv2.VideoCapture(gst_str, cv2.CAP_GSTREAMER)

def open_cam_usb():
	return cv2.VideoCapture("/dev/video1")


def open_window(width, height):
	cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
	cv2.resizeWindow(WINDOW_NAME, width, height)
	cv2.moveWindow(WINDOW_NAME, 0, 0)
	cv2.setWindowTitle(WINDOW_NAME, 'Camera Demo for Jetson TX2/TX1')


def read_cam(cap):
	show_help = True
	full_scrn = False
	help_text = '"Esc" to Quit, "H" for Help, "F" to Toggle Fullscreen'
	font = cv2.FONT_HERSHEY_PLAIN
	while True:
		if cv2.getWindowProperty(WINDOW_NAME, 0) < 0:
			# Check to see if the user has closed the window
			# If yes, terminate the program
			break
		_, img = cap.read() # grab the next image frame from camera
		if show_help:
			cv2.putText(img, help_text, (11, 20), font,
						1.0, (32, 32, 32), 4, cv2.LINE_AA)
			cv2.putText(img, help_text, (10, 20), font,
						1.0, (240, 240, 240), 1, cv2.LINE_AA)
		cv2.imshow(WINDOW_NAME, img)
		key = cv2.waitKey(10)
		if key == 27: # ESC key: quit program
			break
		elif key == ord('H') or key == ord('h'): # toggle help message
			show_help = not show_help
		elif key == ord('F') or key == ord('f'): # toggle fullscreen
			full_scrn = not full_scrn
			if full_scrn:
				cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN,
									  cv2.WINDOW_FULLSCREEN)
			else:
				cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN,
									  cv2.WINDOW_NORMAL)


def main():
	print('OpenCV version: {}'.format(cv2.__version__))
	width = 1280
	height = 720	
	cap = open_cam_onboard(width, height)

	if not cap.isOpened():
		sys.exit('Failed to open camera!')

	open_window(width, height)
	read_cam(cap)

	cap.release()
	cv2.destroyAllWindows()


if __name__ == '__main__':
	main()
