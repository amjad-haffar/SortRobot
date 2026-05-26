
import cv2
import numpy as np
# from ultralytics import YOLO

import torch
# import onnxruntime as ort

GREEN_LOW = np.array([40, 50, 100])
GREEN_HIGH = np.array([90, 255, 255])

RED_LOW1  = np.array([0, 120, 100])
RED_HIGH1 = np.array([8, 255, 255])


class RobotVision:
    def __init__(self,robot,maxspeed,timestep,movement):
        #camera
        self.camera = robot.getDevice("camera")
        self.camera.enable(timestep)
        self.width = self.camera.getWidth()
        self.height = self.camera.getHeight()
        self.frame_center = self.width // 2
        self.MAX_SPEED=maxspeed
        self.movement=movement
        # lock for objects 
        self.locked_class = None
        self.locked_box = None
        self.lock_lost_counter = 0
        self.LOCK_LOST_THRESHOLD = 5  # frames
        
        self.AVOID_DURATION=20
        self.avoid_steps = 0
        self.bin_is_close=False
        #sensors
        self.sensor_left = robot.getDevice("ds0")
        self.sensor_right = robot.getDevice("ds1")
        self.sensor_middle = robot.getDevice("dsm")
        self.sensor_middle.enable(timestep)
        self.sensor_left.enable(timestep)
        self.sensor_right.enable(timestep)
        self.reachedObject = -1
        self.reachedColor = False
        #model
        self.model = torch.hub.load(
            'ultralytics/yolov5',
            'custom',
            path='../best30_windows.pt',
            source='github'
        )
        self.model.conf = 0.35
        self.model.iou = 0.45
        self.model.eval()
        self.class_names = self.model.names
        # onnx
        # self.session = ort.InferenceSession("../bestnew.onnx", providers=["CPUExecutionProvider"])
        # self.input_name = self.session.get_inputs()[0].name
        print(self.class_names)
        print("model loaded")

    def goToColor(self,color):
        if self.bin_is_close == False:
            print()
            if self.obstacle_avoidance():
                return False
        frame = self.get_opencv_image()
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        stop_threshold=0
        min_color_width=50
        if color == "green":
            stop_threshold=200
            min_color_width=50
            mask = cv2.inRange(hsv, GREEN_LOW, GREEN_HIGH)
        elif color == "red":
            stop_threshold=400
            mask = cv2.inRange(hsv, RED_LOW1, RED_HIGH1)
            min_color_width=25

        self.visualize_mask(mask)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if len(contours) > 0:
            goal_object = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(goal_object)
            center_x = x + w // 2
            if w > 400:
                    self.bin_is_close = True
            else:
                self.bin_is_close = False

            if w < min_color_width:
                print(f"{color} detected, this is an object, ignoring")
                self.movement.rotateRight()
                return False
            if abs(center_x - self.frame_center) < 8:
                front_right = self.sensor_right.getValue()
                front_left = self.sensor_left.getValue()
                if front_right > stop_threshold or front_left > stop_threshold:
                    print("color aligned and close stop")
                    self.movement.stop()
                    return True
                else:
                    print("color aligned advancing...")
                    self.movement.forward(self.MAX_SPEED*0.7)
            elif center_x < self.frame_center:
                print("color left")
                self.movement.rotateLeft()
            else:
                print("color right")
                self.movement.rotateRight()
        else:
            print("No color found, rotating...")
            self.bin_is_close = False
            self.movement.rotateRight()
        return False

    def goToObject(self):
        frame = self.get_opencv_image()
        ALIGN_TOLERANCE = 10

        results = self.model(frame)
        detections = results.xyxy[0].cpu().numpy()

        if len(detections) == 0:
            print("No object found, rotating...")
            self.movement.rotateRight()
            self.locked_class = None
            return -1
        
        self.show_debug_frame(frame,detections)
        if not hasattr(self, "locked_class"):
            self.locked_class = None
            self.lock_lost_counter = 0

        if self.locked_class is None:
            # detect
            detections = sorted(
                detections,
                key=lambda d: (d[2] - d[0]) * (d[3] - d[1]),
                reverse=True
            )
            x1, y1, x2, y2, conf, cls = detections[0]
            cls = int(cls)
            # lock object
            self.locked_class = cls
            self.lock_lost_counter = 0
            print(f"Locked on {self.class_names[cls]} conf: {conf}")
        else:
            # when object locked 
            same_class = [d for d in detections if int(d[5]) == self.locked_class]
            if len(same_class) == 0:
                self.lock_lost_counter += 1
                if self.lock_lost_counter > 5:
                    print("Target lost, unlocking")
                    self.locked_class = None
                self.movement.rotateRight()
                return -1

            # choose closest box to center
            same_class = sorted(
                same_class,
                key=lambda d: abs(((d[0] + d[2]) / 2) - self.frame_center)
            )
            x1, y1, x2, y2, conf, cls = same_class[0]
            cls = int(cls)
            self.lock_lost_counter = 0

        label = self.class_names[cls]

        center_x = (x1 + x2) / 2
        dx = center_x - self.frame_center
        box_width = x2 - x1
        box_hight= y2 - y1
        MAX_OBJECT_WIDTH = 120 
        MAX_OBJECT_height = 600
        if box_width > MAX_OBJECT_WIDTH or box_hight > MAX_OBJECT_height:
            print("Ignoring large object (its a bin)")
            return -1

        if abs(dx) < ALIGN_TOLERANCE:
            if box_width > 80:
                print(f"{label} aligned and close stop")
                self.movement.stop()
                return cls
            else:
                print(f"{label} aligned advancing...")
                self.movement.forward(0.4 * self.MAX_SPEED)
        elif center_x < self.frame_center:
            print(f"{label} turning left")
            self.movement.rotateLeft()
        else:
            print(f"{label} turning right")
            self.movement.rotateRight()

        return -1
    #### bonus function, simple avoidence 
    def obstacle_avoidance(self):
        OBSTACLE_CLOSE = 25

        if self.avoid_steps > 0:
            self.avoid_steps -= 1
            print("Avoiding obstacle... going ", self.avoid_dir)
            if self.avoid_dir == "LEFT":
                self.movement.goLeft(self.MAX_SPEED*0.4)
            else:
                self.movement.goRight(self.MAX_SPEED*0.4)

            return True

        # Read sensors
        front = self.sensor_middle.getValue()
        left  = self.sensor_left.getValue()
        right = self.sensor_right.getValue()
        # print("Sensors:", left, front, right)
        if left > OBSTACLE_CLOSE:
            self.avoid_dir = "RIGHT"
        elif right > OBSTACLE_CLOSE:
            self.avoid_dir = "LEFT"
        elif front > OBSTACLE_CLOSE:
            self.avoid_dir = "RIGHT" if left < right else "LEFT"
        else:
            return False

        print("Obstacle detected go ", self.avoid_dir)
        self.avoid_steps = self.AVOID_DURATION
        self.movement.stop()
        return True

    def get_opencv_image(self):
        raw = self.camera.getImage() 
        img = np.frombuffer(raw, np.uint8).reshape((self.height, self.width, 4))  # BGRA
        img = img[:, :, :3]  # remove alpha
        return img
 
    def visualize_mask(self,mask):
        cv2.namedWindow("Camera View", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Camera View", 600, 600)
        cv2.imshow("Camera View", mask)
        cv2.waitKey(32)

    def show_debug_frame(self, frame, dets):
        img = frame.copy()

        for det in dets:
            x1, y1, x2, y2, conf, cls = det
            label = f"{self.class_names[int(cls)]} {conf:.2f}"

            # Draw rectangle
            cv2.rectangle(
                img,
                (int(x1), int(y1)),
                (int(x2), int(y2)),
                (0, 255, 0),
                2
            )
            
            # Draw label
            cv2.putText(
                img,
                label,
                (int(x1), int(y1) - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )
        cv2.imshow("YOLO Debug View", img)
        cv2.waitKey(1)
        
    #### I exported my model using onnx instead of torch ####
    #### (this failed to detect Bottles) dont run this ####
    # def preprocess(self, frame):
    #     img = cv2.resize(frame, (640, 640))
    #     img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    #     img = img.astype(np.float32) / 255.0
    #     img = np.transpose(img, (2, 0, 1))  # HWC → CHW
    #     img = np.expand_dims(img, 0)        # NCHW
    #     return img

    # def infer(self, frame):
    #     inp = self.preprocess(frame)
    #     outputs = self.session.run(None, {self.input_name: inp})
    #     pred = outputs[0]  # should be [1,25200,7] or [25200,7]
    #     return pred
    # def goToObject(self):
    #     frame = self.get_opencv_image()
    #     ALIGN_TOLERANCE=30
    #     pred = self.infer(frame)
    #     detections = self.nms_onnx(pred)
    #     self.debug_counter = (self.debug_counter + 1) % 3
    #     if self.debug_counter == 0:
    #         self.show_debug_frame(frame, detections)
    #     if len(detections) > 0:
    #         # Pick largest detection
    #         detections = sorted(detections, key=lambda d: (d[2]-d[0])*(d[3]-d[1]), reverse=True)
    #         x1, y1, x2, y2, conf, cls = detections[0]
    #         label = self.class_names[int(cls)]
    #         if label == "bottle" or label == "can":
    #             center_x = (x1 + x2) / 2
    #             dx = center_x - self.frame_center
    #             box_width = x2 - x1
    #             if abs(dx) < ALIGN_TOLERANCE:
    #                 if box_width > 80:
    #                     print("Object aligned and close — stopping.")
    #                     self.movement.stop()
    #                     return cls
    #                 else:
    #                     print("Object aligned — advancing.")
    #                     self.movement.forward(0.4 * self.MAX_SPEED)
    #             elif center_x < self.frame_center:
    #                 print("Object left, turning left.")
    #                 self.movement.rotateLeft()
    #             else:
    #                 print("Object right, turning right.")
    #                 self.movement.rotateRight()
    #         else:
    #             print("Non-trash object detected, ignoring.")
    #             self.movement.rotateRight()
    #     else:
    #         print("No object found, rotating to search.")
    #         self.movement.rotateRight()
    #     return -1

    # def nms_onnx(self, preds, conf_thres=0.3, iou_thres=0.45):
    #     preds = preds[0]  # (25200, 7)
        
    #     boxes = preds[:, :4]
    #     scores = preds[:, 4]
    #     classes = preds[:, 5]

    #     # confidence mask
    #     mask = scores > conf_thres
    #     boxes = boxes[mask]
    #     scores = scores[mask]
    #     classes = classes[mask]

    #     if len(boxes) == 0:
    #         return []

    #     # Convert xywh → xyxy
    #     xyxy = np.zeros_like(boxes)
    #     xyxy[:, 0] = boxes[:, 0] - boxes[:, 2] / 2
    #     xyxy[:, 1] = boxes[:, 1] - boxes[:, 3] / 2
    #     xyxy[:, 2] = boxes[:, 0] + boxes[:, 2] / 2
    #     xyxy[:, 3] = boxes[:, 1] + boxes[:, 3] / 2

    #     # Apply NMS
    #     idxs = cv2.dnn.NMSBoxes(
    #         xyxy.tolist(), scores.tolist(), conf_thres, iou_thres
    #     )

    #     if len(idxs) == 0:
    #         return []

    #     idxs = idxs.flatten()

    #     detections = []
    #     for i in idxs:
    #         detections.append([
    #             xyxy[i][0],
    #             xyxy[i][1],
    #             xyxy[i][2],
    #             xyxy[i][3],
    #             float(scores[i]),
    #             int(classes[i])
    #         ])
    #     return detections
