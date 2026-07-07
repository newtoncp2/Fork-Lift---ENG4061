import cv2

CHESSBOARD_SIZE = (8, 5)

criteria = (
    cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
    5000,
    0.000001
)

cap = cv2.VideoCapture(2, cv2.CAP_V4L2)  # Use V4L2 backend for Raspberry Pi
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320) # lower resolution for faster processing
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1) # Set buffer size to 1 to reduce latency
cap.set(cv2.CAP_PROP_FPS, 15)
ind = 0

while ind < 30:  
    ret, frame = cap.read()
    if not ret:
        break
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    ret, corners = cv2.findChessboardCorners(
        gray,
        CHESSBOARD_SIZE,
        None
    )
    
    if ret:
        # Refina precisão subpixel
        corners2 = cv2.cornerSubPix(
            gray,
            corners,
            (11, 11),
            (-1, -1),
            criteria
        )
        
        cv2.drawChessboardCorners(
            frame,
            CHESSBOARD_SIZE,
            corners2,
            ret
        )
    
    cv2.imshow('Camera Feed', frame)

    if cv2.waitKey(1) & 0xFF == ord('c'):
        cv2.imwrite('calibration_images/captured_image'+str(ind)+'.jpg', frame)
        print("Image captured and saved as 'captured_image.jpg'") 
        ind += 1