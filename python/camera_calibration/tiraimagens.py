import cv2


cap = cv2.VideoCapture(-1, cv2.CAP_V4L2)  # Use V4L2 backend for Raspberry Pi
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320) # lower resolution for faster processing
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1) # Set buffer size to 1 to reduce latency
cap.set(cv2.CAP_PROP_FPS, 15)
ind = 0

while ind < 30:  
    ret, frame = cap.read()
    if not ret:
        break
    
    cv2.imshow('Camera Feed', frame)

    if cv2.waitKey(1) & 0xFF == ord('c'):
        cv2.imwrite('calibration_images/captured_image'+str(ind)+'.jpg', frame)
        print("Image captured and saved as 'captured_image.jpg'") 
        ind += 1