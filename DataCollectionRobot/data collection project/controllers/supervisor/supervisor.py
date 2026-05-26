"""youBot controller."""

# You may need to import some classes of the controller module. Ex:
# from controller import Robot, Motor, DistanceSensor
# from controller import Robot, DistanceSensor

from controller import Supervisor
import numpy as np
import random
import math
import warnings
import os

warnings.filterwarnings("ignore", category=FutureWarning)

supervisor = Supervisor()
# this will produce an error
# you need to adjust the world files to import camera devices 
# and that will crash with the original controller
camera = supervisor.getDevice("youbot_camera")
cam_node = supervisor.getFromDef("CAMERA")
camera.enable(32)
camera.recognitionEnable(32)
print(camera)
print(cam_node)

arm1 = supervisor.getDevice("arm1")
arm2 = supervisor.getDevice("arm2")
arm3 = supervisor.getDevice("arm3")
arm4 = supervisor.getDevice("arm4")
arm5 = supervisor.getDevice("arm5")
# put the arm away
def setArm():
    arm3.setPosition(+2.50) 
    arm2.setPosition(+1.13)   
    arm4.setPosition(-1.6)

width = camera.getWidth()
height = camera.getHeight()
frame_center = width // 2

# vision
can1 = supervisor.getFromDef("CAN1")   
can1_translation = can1.getField("translation")

can2 = supervisor.getFromDef("CAN2")   
can2_translation = can2.getField("translation")

beer1 = supervisor.getFromDef("BEER1")   
beer1_translation = beer1.getField("translation")

beer2 = supervisor.getFromDef("BEER2")  
beer2_translation = beer2.getField("translation")

save_dir = "C:/Users/LENOVO/Desktop/ARAI/dataset"
os.makedirs(save_dir, exist_ok=True)
objects=[
(can1,1),
(can2,1),
(beer1,0),
(beer2,0)
]

CAN_RADIUS = 0.03
CAN_HEIGHT = 0.12
 
BOTTLE_RADIUS = 0.031 
BOTTLE_HEIGHT = 0.24 

def world_to_camera(point, cam_node):
    cam_pos = np.array(cam_node.getPosition())      #  world coords
    R_wc = np.array(cam_node.getOrientation()).reshape(3, 3)  # local to world
    R_cw = R_wc.T                                             # world to local

    p_rel = np.array(point) - cam_pos
    p_cam = R_cw @ p_rel
    return p_cam[0], p_cam[1], p_cam[2]

def project_point(point, camera, cam_node):
    img_w, img_h = camera.getWidth(), camera.getHeight()
    fov_x = camera.getFov()  # horizontal FOV in radians

    # Focal lengths
    fx = img_w / (2.0 * math.tan(fov_x / 2.0))

    # Webots doc: vertical FOV = fieldOfView * height / width
    fov_y = fov_x * img_h / img_w
    fy = img_h / (2.0 * math.tan(fov_y / 2.0))

    cx, cy = img_w / 2.0, img_h / 2.0

    X_cam, Y_cam, Z_cam = world_to_camera(point, cam_node)

    depth = X_cam
    if depth <= 0:
        return None  # behind camera


    u = cx - fx * (Y_cam / depth)
    v = cy - fy * (Z_cam / depth)

    return [u, v]


def getBox(node, camera, cam_node, class_id=1):
    x, y, z = node.getPosition()
    center = [x, y, z]
    
    print("center in camera frame:", world_to_camera(center, cam_node))
    angles = [0, math.pi / 2, math.pi, 3 * math.pi / 2]
    pts = []
    for a in angles:
        if class_id==1:
            dx = CAN_RADIUS * math.cos(a)
            dy = CAN_RADIUS * math.sin(a)
            pts.append([x + dx, y + dy, z])               # bottom
            pts.append([x + dx, y + dy, z + CAN_HEIGHT])  # top
        else:
            dx = BOTTLE_RADIUS * math.cos(a)
            dy = BOTTLE_RADIUS * math.sin(a)
            pts.append([x + dx, y + dy, z])               # bottom
            pts.append([x + dx, y + dy, z + BOTTLE_HEIGHT])  # top
        

    pixels = [project_point(p, camera, cam_node) for p in pts]
    pixels = [p for p in pixels if p is not None]
    if not pixels:
        return None

    xs = [p[0] for p in pixels]
    ys = [p[1] for p in pixels]

    img_w, img_h = camera.getWidth(), camera.getHeight()

    x_min, x_max = max(0, min(xs)), min(img_w - 1, max(xs))
    y_min, y_max = max(0, min(ys)), min(img_h - 1, max(ys))

    # If the entire box is outside the camera view, skip
    if x_max <= x_min or y_max <= y_min:
        return None

    x_center = ((x_min + x_max) / 2.0) / img_w
    y_center = ((y_min + y_max) / 2.0) / img_h
    width = (x_max - x_min) / img_w
    height = (y_max - y_min) / img_h

    return f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}"



def randomPlace():
    new_x = random.uniform(+4, +2)   
    new_y = random.uniform(-4, -2)
    new_z = 0.00   # hight
    return [new_x, new_y, new_z]


counter = 3000
frame_id = 3000
setArm()


while supervisor.step(32) != -1:
    counter += 1
    if counter % 20 == 0:
        frame_id += 1
        # Randomize positions
        can1.getField("translation").setSFVec3f(randomPlace())
        can2.getField("translation").setSFVec3f(randomPlace())
        beer1.getField("translation").setSFVec3f(randomPlace())
        beer2.getField("translation").setSFVec3f(randomPlace())

        # fixed roation for all
        can1.getField("rotation").setSFRotation([0, 0, 1, 0])
        can2.getField("rotation").setSFRotation([0, 0, 1, 0])
        beer1.getField("rotation").setSFRotation([0, 0, 1, 0]) 
        beer2.getField("rotation").setSFRotation([0, 0, 1, 0])

        # Save image
        img_name = f"frame_{frame_id}.png"
        img_path = os.path.join(save_dir, img_name)
        camera.saveImage(img_path, 100)

        # Save YOLO labels 
        txt_name = img_name.replace(".png", ".txt")
        txt_path = os.path.join(save_dir, txt_name)

        with open(txt_path, "w") as f:
            for node,id in objects:
                bbox = getBox(node, camera, cam_node, class_id=id)
                print(f"Node {node.getDef()} bbox: {bbox}") 
                if bbox:
                    f.write(bbox + "\n")



