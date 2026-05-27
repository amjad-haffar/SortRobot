#  Waste Sorting Robot using Kuka YouBot and YOLOv5

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Webots](https://img.shields.io/badge/Webots-Robotics%20Simulation-orange.svg)](https://cyberbotics.com/)
[![YOLOv5](https://img.shields.io/badge/YOLOv5-Object%20Detection-green.svg)](https://github.com/ultralytics/yolov5)
[![OpenCV](https://img.shields.io/badge/OpenCV-Computer%20Vision-red.svg)](https://opencv.org/)

A university robotics project focused on autonomous object detection, collection, and sorting using a simulated robot in **Webots**.

# Features
- Autonomous object detection using YOLOv5
- Webots robotic simulation
- Robotic arm grabbing sequence
- Object approach and alignment logic
- Basket color recognition
- Autonomous item sorting
- Simple obstacle avoidance
- Data collection and dataset generation
- fine tuning on YOLOv5

The robot is capable of detecting recyclable objects, approaching them, grabbing them using a robotic arm, and sorting them into different baskets based on object type.

---

# Project Overview

The system uses a trained **YOLOv5s** model for object detection and recognition inside a Webots simulation environment.

Detected objects include:
- cans
- bottles

The robot performs the following sequence autonomously:

1. Scan the environment using the camera
2. Detect an object using YOLOv5
3. Navigate toward the object
4. Align with the target
5. Perform robotic arm movement
6. Grab the object
7. Navigate toward the correct basket
8. Detect basket color using color contour detection
9. Drop the object into the correct basket
10. Repeat the process
#Work Flow
<img width="1693" height="929" alt="88462190-7cce-4df8-b474-fee284656ca1" src="https://github.com/user-attachments/assets/9e44864a-62b6-45f9-93e6-4b05972e11a3" />
---

# Sorting Logic

The robot sorts objects into colored baskets:

- **Can → Green Basket**
- **Bottle → Red Basket**

Basket detection is performed using camera-based color contour techniques.

---


# Data Collection and Training

A separate module was developed for data collection and training preparation.

The dataset includes:
- can images
- bottle images

The model was trained using:
- **YOLOv5s (small version)**
- you can find the training notebook in "Waste Sort YouBot\SortSoldierRobot\controllers\training notebook.ipynb"

Approximate confidence results:
- **Cans:** ~60-70%
- **Bottles:** ~80–90%
Note: the original model was able to detetect bottles without the fine tuning 
---

# Technologies Used

- Python
- Webots
- YOLOv5
- OpenCV
- Computer Vision
- Robotics Simulation

---

# Obstacle Avoidance

The project contains a basic obstacle avoidance implementation.

The current implementation is simple and experimental, but it provides a foundation for future improvements and more advanced navigation techniques.

---

# Screenshots

## Object Detection and Picking

<img width="860" height="506" alt="can picking" src="https://github.com/user-attachments/assets/c80d73b4-2dbf-436a-a07e-b60195af16d6" />


---

## Item Sorting
<img width="909" height="445" alt="sorting" src="https://github.com/user-attachments/assets/85ac1112-e113-462c-873d-6ff7a0ee9444" />


---

## Item Dropping
<img width="738" height="472" alt="dropping" src="https://github.com/user-attachments/assets/9fb9ee55-1c5c-4e41-b618-3f5a0e373ba1" />


---

## Data Collection and Training
<img width="943" height="644" alt="data collection" src="https://github.com/user-attachments/assets/08e5f471-6885-406d-ab49-6e57c1f88aa3" />


---

# Notes

This project was developed as part of my MSc in Artificial Intelligence at Sheffield Hallam University.
The system is experimental and intended for educational and research purposes.

## Acknowledgments
**Developed By:** [Amjad Alhaffar](https://www.linkedin.com/in/amjadalhaffarsyr/)

**Supervisor: Dr. Samuele Vinanzi**

### Sheffield Hallam University

<img width="280" height="188" alt="uni logo" src="https://github.com/user-attachments/assets/6a9dd6f2-756d-48b9-978b-20636fc2a57d" />
