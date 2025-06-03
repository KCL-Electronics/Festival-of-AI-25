import cv2

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("FAIL! Failed to open camera.")
    exit()

ret, frame = cap.read()
if ret:
    cv2.imwrite("test_frame.jpg", frame)
    print("PASS! Frame captured. Check 'test_frame.jpg'")
else:
    print("FAIL! Failed to read frame.")

cap.release()
