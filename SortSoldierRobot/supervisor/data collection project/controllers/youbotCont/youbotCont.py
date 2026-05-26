"""youBot controller."""

# You may need to import some classes of the controller module. Ex:
#  from controller import Robot, Motor, DistanceSensor

from controller import Robot,DistanceSensor
from movement import RobotMovement  
from arms import RobotArms  
from vision import RobotVision  
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
    
robot = Robot()
timestep = int(robot.getBasicTimeStep())  
movement = RobotMovement(robot)  
MAX_SPEED=movement.MAX_SPEED
arms_movement=RobotArms(robot,MAX_SPEED,movement)
# hide arm to avoide getting shadows from it
arms_movement.hide_arm()
robotVision= RobotVision(robot,MAX_SPEED,timestep,movement,)
state = "SEARCH" # "SEARCH", "GRAB","BIN", "RELEASE","DEBUG"

# initialise just in case 
robotVision.reachedObject=-1
robotVision.reachedColor=False
arms_movement.grabbed=False
print("loop start")
frame_count=0
while robot.step(timestep) != -1:
    # if state== "DEBUG":
        # movement.goRight(MAX_SPEED)
        
    ### skip for speed test ###
    # frame_count+=1
    # if frame_count % 100 == 0:
        # continue
        
    #### Detect objects ####
    if state == "SEARCH":
        if robotVision.reachedObject != -1:
            movement.stop()
            state="GRAB"
        else:
            robotVision.reachedObject = robotVision.goToObject()
    #### Grabbing ####
    elif state == "GRAB":
        if arms_movement.grabbed: # after grabing any object => change state 
            state = "BIN"
        else:
            if robotVision.reachedObject == 0: # 0 class => bottle
                # print("bottle")
                arms_movement.grabbed= arms_movement.grab_bottle()
            elif robotVision.reachedObject == 1: # 1 class => can
                # print("can")
                arms_movement.grabbed= arms_movement.grab_can()

    #### Detect Bins ####    
    elif state == "BIN":
        if robotVision.reachedColor:
                movement.stop()
                state= "RELEASE"
        else:
            if robotVision.reachedObject == 0 : # 0 class => put bottle in red
                robotVision.reachedColor = robotVision.goToColor("red")
            elif robotVision.reachedObject == 1: # 1 class => put can in green
                robotVision.reachedColor = robotVision.goToColor("green")
    #### Release object ####
    elif state == "RELEASE":
        if arms_movement.releaseItem():
            arms_movement.grabbed = False
            print("done")
            state = "SEARCH"
            arms_movement.grabbed = False
            robotVision.reachedObject = -1
            robotVision.reachedColor = False
     #### Note ####
     #    there is no end, you can copy one of the bottles
     #    or cans and place them randomly 
     #    to test how youbot detect it 

            