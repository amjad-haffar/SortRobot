"""youBot controller."""

# You may need to import some classes of the controller module. Ex:
#  from controller import Robot, Motor, DistanceSensor

from controller import Robot,DistanceSensor
import numpy as np
import cv2
import torch

import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

# Load YOLOv5 small pretrained on COCO
model = torch.hub.load('ultralytics/yolov5', 'yolov5s')

    
robot = Robot()
timestep = int(robot.getBasicTimeStep())  # rad/s
#camera
camera = robot.getDevice("camera")
camera.enable(timestep)
width = camera.getWidth()
height = camera.getHeight()
frame_center = width // 2

#vision
def get_opencv_image(robot_camera):
    raw = robot_camera.getImage() # returns a flat byte buffer (i.e., a 1D array of bytes).
    img = np.frombuffer(raw, np.uint8).reshape((height, width, 4))  # BGRA
    img = img[:, :, :3]  # Remove alpha (BGR)
    return img
    
def visualize_mask(mask):
    cv2.namedWindow("Camera View", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Camera View", 600, 300)
    cv2.imshow("Camera View", mask)
    cv2.waitKey(timestep)

#sensors
sensor_left = robot.getDevice("ds0")
sensor_right = robot.getDevice("ds1")
sensor_left.enable(timestep)
sensor_right.enable(timestep)

#wheels
def initWheel(name):
    wheel=robot.getDevice(name)
    wheel.setPosition(float('inf'))  # infinite position = velocity mode
    wheel.setVelocity(0)
    # wheel.setAvailableTorque(7.0)
    return wheel
    
frontR=initWheel("wheel1")
frontL=initWheel("wheel2")
backR=initWheel("wheel3")
backL=initWheel("wheel4")
# arm 
arm1 = robot.getDevice("arm1")
arm2 = robot.getDevice("arm2")
arm3 = robot.getDevice("arm3")
arm4 = robot.getDevice("arm4")
arm5 = robot.getDevice("arm5")

# Put arm in a low resting pose
arm1.setPosition(0.0)   # rotate base joint
arm2.setPosition(1.57)  # lift downwards (90°)
arm3.setPosition(-2.0)  # fold inward
arm4.setPosition(1.3)   # adjust wrist
arm5.setPosition(0.0)   # gripper orientation


#movement
wheels = [frontR, frontL, backR, backL]
MAX_SPEED = min(w.getMaxVelocity() for w in wheels)

def rotateLeft(speed= 0.3*MAX_SPEED):
    frontR.setVelocity(+speed)
    backR.setVelocity(+speed)
    frontL.setVelocity(-speed)
    backL.setVelocity(-speed)
    
def rotateRight(speed= 0.3*MAX_SPEED):
    frontR.setVelocity(-speed)
    backR.setVelocity(-speed)
    frontL.setVelocity(+speed)
    backL.setVelocity(+speed)
    
def goLeft(speed):
    frontR.setVelocity(+speed)
    backR.setVelocity(-speed)
    frontL.setVelocity(-speed)
    backL.setVelocity(+speed)

def goRight(speed=0.2*MAX_SPEED):
    frontR.setVelocity(+spee)
    backR.setVelocity(+speed)
    frontL.setVelocity(+speed)
    backL.setVelocity(-speed)
    
def forward(speed=0.2*MAX_SPEED):
    frontR.setVelocity(+speed)
    backR.setVelocity(+speed)
    frontL.setVelocity(+speed)
    backL.setVelocity(+speed)
    
def backward(speed):
    frontR.setVelocity(-speed)
    backR.setVelocity(-speed)
    frontL.setVelocity(-speed)
    backL.setVelocity(-speed)
    
def stop():
    frontR.setVelocity(0)
    backR.setVelocity(0)
    frontL.setVelocity(0)
    backL.setVelocity(0)
    
#control speed
# speed = (1 - alpha) * speed + alpha * speed_target
# speed_target = 1 * MAX_SPEED
# speed = 0.0
# alpha = 0.02

#robot programming
reachedYellow = False
def goToYellow():
    frame = get_opencv_image(camera)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    # Yellow mask
    lower_yellow = np.array([20, 200, 100])
    upper_yellow = np.array([30, 255, 255])
    mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
    visualize_mask(mask)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if len(contours) > 0:
        goal_object = contours[0]
        x, y, w, h = cv2.boundingRect(goal_object)
        center_x = x + w // 2

        if abs(center_x - frame_center) < 5:
            front_right = sensor_right.getValue()
            front_left = sensor_left.getValue()
            print("||||||||||||||||||||||front_right", front_right) 
            print("||||||||||||||||||||||front_left", front_left)
            if front_right > 220 or front_left > 220:
                print("Object aligned and close — stopping.")
                stop()
                return True
            else:
                print("Object aligned — advancing.")
                forward(MAX_SPEED)
        elif center_x < frame_center:
            print("Object left, turning left.")
            rotateLeft()
        else:
            print("Object right, turning right.")
            rotateRight()
    else:
        print("No object found, rotating to search.")
        rotateRight()
    return False

reachedObject = False
def goToObject():
    frame = get_opencv_image(camera)
    results = model(frame)
    detections = results.xyxy[0].cpu().numpy()

    if len(detections) > 0:
        # Pick largest detection
        detections = sorted(detections, key=lambda d: (d[2]-d[0])*(d[3]-d[1]), reverse=True)
        x1, y1, x2, y2, conf, cls = detections[0]
        label = model.names[int(cls)]

        if label in ["bottle", "cup", "can"]:
            center_x = (x1 + x2) / 2
            box_width = x2 - x1
            # print(box_width)

            if abs(center_x - frame_center) < 5:
                print(center_x - frame_center)
                front_right = sensor_right.getValue()
                front_left = sensor_left.getValue()
                if front_right > 220 or front_left > 220 or box_width > 150:
                    # print("Object aligned and close — stopping.")
                    stop()
                    return True
                else:
                    # print("Object aligned — advancing.")
                    forward(0.4 * MAX_SPEED)
            elif center_x < frame_center:
                print("Object left, turning left.")
                rotateLeft()
            else:
                print("Object right, turning right.")
                rotateRight()
        # else:
            # print("Non-trash object detected, ignoring.")
            # rotateRight()
    else:
        print("No object found, rotating to search.")
        rotateRight()

    return False

state = "SEARCH" ### "SEARCH", "APPROACH" ,"BIN","DONE"
print("loop start")
while robot.step(timestep) != -1:
    #### detect bins ####
    # if reachedYellow:
        # stop()
        # continue
    # reachedYellow = goToYellow()
    
    #### detect objects ####
    if reachedObject:
        stop()
        # Here you can trigger arm/gripper logic
        continue
    else:
        reachedObject = goToObject()