import cv2


cap = cv2.VideoCapture(0)
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