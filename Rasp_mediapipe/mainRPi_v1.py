import cv2
import mediapipe as mp
import time
import serial

ser=serial.Serial(
    port='/dev/ttyUSB0',
    baudrate=9600,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=0)
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_holistic = mp.solutions.holistic

pose_all = 33
duration=0
timelist=[]
dlist1=[]
dlist2=[]
vlist1=[]
vlist2=[]
alist1=[]
alist2=[]

# For webcam input:
cap = cv2.VideoCapture(0)
cap.set(3, 320)
cap.set(4, 240)
with mp_holistic.Holistic(
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5) as holistic:
    while cap.isOpened():
        success, image = cap.read()
        if not success:
            print("Ignoring empty camera frame.")
            # If loading a video, use 'break' instead of 'continue'.
            continue

        # To improve performance, optionally mark the image as not writeable to
        # pass by reference.
        image.flags.writeable = False
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = holistic.process(image)

        # Draw landmark annotation on the image.
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        
        mp_drawing.draw_landmarks(
            image,
            results.pose_landmarks,
            mp_holistic.POSE_CONNECTIONS,
            landmark_drawing_spec=mp_drawing_styles
                .get_default_pose_landmarks_style())

        pose_landmarkLD_x = []
        pose_landmarkLD_y = []
        pose_landmarkLD_z = []
        if results.pose_landmarks:
            for landmark in results.pose_landmarks.landmark:
                pose_landmarkLD_x.append(landmark.x)
                pose_landmarkLD_y.append(landmark.y)              
                pose_landmarkLD_z.append(landmark.z)
            
            for z in pose_landmarkLD_z:
                print("z: ", z)
            
            sum_x = 0
            sum_y = 0
            for x in pose_landmarkLD_x:
                sum_x += x
                
            pose_landmarkLD_y.sort()
            for i in range(11):    # 0~10: Face Landmarks
                sum_y += pose_landmarkLD_y[i]
                
            mean_x = sum_x / len(pose_landmarkLD_x)
            mean_y = sum_y / 11
            print("mean_x: ", mean_x, "mean_y: ", mean_y)
            
            if (mean_x - 0.5 > 0.15):
                ser.write(b'r')    # turn right
            elif (mean_x - 0.5 < -0.1):
                ser.write(b'l')    # turn left
            else:
                ser.write(b'f')    # stay front
                
            if (mean_y - 0.5 > 0.1):
                ser.write(b'u')    # neck up
            elif (mean_y - 0.5 < -0.15):
                ser.write(b'd')    # neck down
            else:
                ser.write(b's')    # neck stop
                    
        else:    # if no results.pose_landmarks
            for i in range(pose_all):
                pose_landmarkLD_x.append(-1)
                pose_landmarkLD_y.append(-1)
                pose_landmarkLD_z.append(0)

        
        
        #시간 확인
        newtime=time.time()

        #첫 시간을 확인한 경우(시간 리스트에 아무것도 없는 경우)
        if len(timelist)==0:
            timelist.append(newtime)
        #시간 리스트에 적어도 하나의 원소가 있는 경우
        elif len(timelist)>0:
            #시간 리스트의 마지막 원소와 마지막에서 두 번째 원소 사이의 시간차를 duration으로 계산
            duration=newtime-timelist[len(timelist)-1]

            #duration이 0.5이상이면 속도, 가속도 계산하여 변위 속도 가속도(dlist, vlist, alist 원소) 계산
            if duration>=1:
                timelist.append(newtime)

                #변위 계산
                dlist1.append(abs(pose_landmarkLD_y[12]-pose_landmarkLD_y[24]))
                dlist2.append(abs(pose_landmarkLD_y[11]-pose_landmarkLD_y[23]))

                #속도 계산
                if len(dlist1)>=2:
                    vlist1.append(abs(dlist1[len(dlist1)-1]-dlist1[len(dlist1)-2])/duration)
                    vlist2.append(abs(dlist2[len(dlist2)-1]-dlist2[len(dlist2)-2])/duration)

                    # 속도가 0.3 이상이면 help 프린트
                    if vlist1[len(vlist1) - 1] > 0.2 or vlist2[len(vlist2) - 1] > 0.2:
                        print("help")
                        ser.write(b'h')
                """#가속도 계산
                if len(vlist1)>=2:
                    alist1.append(abs(vlist1[len(vlist1)-1]-vlist1[len(vlist1)-2])/duration)
                    alist2.append(abs(vlist2[len(vlist2)-1]-vlist2[len(vlist2)-2])/duration)"""


        # Flip the image horizontally for a selfie-view display.
        cv2.imshow('MediaPipe Holistic', cv2.flip(image, 1))

        if cv2.waitKey(5) & 0xFF == ord('q'):
            break
cap.release()
cv2.destroyAllWindows()