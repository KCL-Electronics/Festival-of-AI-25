import cv2
import datetime

def main():

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open camera.")
        return
    else:
        print("Working")

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    cv2.namedWindow('USB Camera - CCTV Mode', cv2.WINDOW_NORMAL)

    cv2.setWindowProperty('USB Camera - CCTV Mode', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    blink_counter = 0  
    show_text = True  

    while True:

        ret, frame = cap.read()

        if not ret:
            print("Error: Failed to capture image")
            break

        num_lines = 4
        height, width = frame.shape[:2]

        font = cv2.FONT_HERSHEY_SIMPLEX
        text = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        position = (10, 30)

        cv2.putText(frame, text, position, font, 0.5, (255, 255, 255), 4, cv2.LINE_AA)

        cv2.putText(frame, text, position, font, 0.5, (0, 0, 255), 2, cv2.LINE_AA)

        if blink_counter % 30 < 15:  
            show_text = True
        else:
            show_text = False

        text = "Location: Arena"
        (text_width, text_height), _ = cv2.getTextSize(text, font, 0.5, 2)

        if show_text:
            cv2.putText(frame, text, (width - text_width - 10, 30), font, 0.5, (0, 255, 255), 2, cv2.LINE_AA)

        blink_counter += 1  

        cv2.imshow('USB Camera - CCTV Mode', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()