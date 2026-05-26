class RobotArms:
    def __init__(self,robot,maxspeed,movement):
        # arm 
        self.robot=robot
        self.arm1 = robot.getDevice("arm1")
        self.arm2 = robot.getDevice("arm2")
        self.arm3 = robot.getDevice("arm3")
        self.arm4 = robot.getDevice("arm4")
        self.arm5 = robot.getDevice("arm5")
        self.fingerL = robot.getDevice("finger::left")
        self.fingerR = robot.getDevice("finger::right")
        # sensors
        self.sensor_middle = robot.getDevice("dsm")
        self.sensor_middle.enable(32)
        # self.fingerL_sensor = robot.getDevice("finger::leftsensor")
        # self.fingerR_sensor = robot.getDevice("finger::rightsensor")
        # self.fingerL_sensor.enable(32)
        # self.fingerR_sensor.enable(32)

        self.fingerL.setAvailableForce(30)
        self.fingerR.setAvailableForce(30)
        # speed control
        self.step = 0           # internal sub-state
        self.timer = 0          # countdown in timesteps
        self.MAX_SPEED=maxspeed
        self.movement=movement
        self.grabbed=False
        # default arm posisiton
    def resetArms(self):
        self.arm1.setPosition(0.0)   
        self.arm2.setPosition(0.0) 
        self.arm3.setPosition(0.0)   
        self.arm4.setPosition(0.0)
        self.arm5.setPosition(0.0)
    #### arms doc ####
    #  arm 1 xx 0.0
    #  arm 2 (-1.13 <-> 1.57)
    #  arm 3 (-2.64 <-> 2.55)
    #  arm 4 (-1.78 <-> 1.78)
    #  arm 5 xx 0.0
    #  fingers max is 0.025
    def hide_arm(self):
        self.arm2.setPosition(1.57)   
        self.arm3.setPosition(0) 
        self.arm4.setPosition(0)
        self.fingerL.setPosition(0.025)
        self.fingerR.setPosition(0.025)
        self._start_timer(1000)

    def arm_pre_grasp(self):
        # self.arm1.setPosition(0.0)     
        self.arm2.setPosition(-1.13)    
        self.arm3.setPosition(-2.2)    
        self.arm4.setPosition(1.78)    
        # self.arm5.setPosition(0.0)   
        self.fingerL.setPosition(0.025)
        self.fingerR.setPosition(0.025)
        
    def pre_grasp_can(self):
        self.fingerL.setVelocity(1)
        self.fingerR.setVelocity(1)
        self.arm2.setPosition(-1.13)  
        self.arm3.setPosition(-2.2)   
        self.arm4.setPosition(1.78)   
        self.fingerL.setPosition(0.025)
        self.fingerR.setPosition(0.025)

    def arm_lower_to_can(self):
        self.arm2.setPosition(-1.13)   
        self.arm3.setPosition(-0.5)    
        self.arm4.setPosition(-1.25)   
          # wrist down
    def micro_forward(self):
        speed = 0.05 * self.MAX_SPEED
        self.movement.frontR.setVelocity(speed)
        self.movement.backR.setVelocity(speed)
        self.movement.frontL.setVelocity(speed)
        self.movement.backL.setVelocity(speed)
    def close_gripper(self):
        self.fingerL.setVelocity(0.01)
        self.fingerR.setVelocity(0.01)
        self.fingerL.setPosition(0.0)
        self.fingerR.setPosition(0.0)
    def arm_release(self):
        self.arm2.setPosition(-1.13)    
        self.arm3.setPosition(0)    
        self.arm4.setPosition(0)  
    def finger_release(self):
        self.fingerL.setVelocity(1)
        self.fingerR.setVelocity(1)
        self.fingerL.setPosition(0.025)
        self.fingerR.setPosition(0.025)
    def arm_lift(self):
        self.arm2.setPosition(0)
        self.arm3.setPosition(0)
        
    def grab_bottle(self):
        if self.step == 0:
            print("Moving to grasp pose...")
            self.arm_pre_grasp()
            self._start_timer(2000)
            self.step = 1
            return False
        if not self._tick_timer():
            return False

        if self.step == 1:
            print("Slow forward...")
            self.movement.forward(0.05 * self.MAX_SPEED)
            sensorVal = self.sensor_middle.getValue()
            print("sensorVal", sensorVal)
            if sensorVal > 63:
                print("Object is close enough!")
                self.movement.stop()
                self.step = 2
                self._start_timer(2000)
                return False
            return False

        if self.step == 2:
            self.movement.stop()
            print("Closing gripper...")
            self.close_gripper()
            self._start_timer(2000)
            self.step = 3
            return False

        if self.step == 3:
            print("Lifting the bottle...")
            self.arm_lift()
            self._start_timer(2000)
            self.step = 4
            return False

        if self.step == 4:
            print("Bottle grab successful")
            self.step = 0  
            return True

    def grab_can(self):
        if self.step == 0:
            print("Moving to grasp pose...")
            self.pre_grasp_can()
            self._start_timer(2000)
            self.step = 1
            return False
        
        if not self._tick_timer():
            return False
        
        if self.step == 1:
            print("Slow forward...")
            self.movement.forward(0.05 * self.MAX_SPEED)
            sensorVal = self.sensor_middle.getValue()
            print("sensorVal", sensorVal)
            if sensorVal > 63:
                print("Object is close enough!")
                self.movement.stop()
                self.step = 2
                self._start_timer(1000)
                return False
            return False
        if self.step == 2:            
            print("Lowering arm to can height...")
            self.arm_lower_to_can()
            self._start_timer(3000)
            self.step = 3
            return False
        
        if self.step == 3:   
            self.movement.stop()
            print("Closing gripper...")
            self.close_gripper()
            self._start_timer(3000)
            self.step = 4
            return False
        
        if self.step == 4:   
            print("Lifting the can...")
            self.arm_lift()
            self._start_timer(2000)
            self.step = 5
            return False
        
        if self.step == 5:
            print("Grab successful")
            self.step = 0  
            return True

    def releaseItem(self):
        if self.step == 0:
            print("release pose...")
            self.arm_release()
            self._start_timer(3000)
            self.step = 1
            return False
        if not self._tick_timer():
            return False
        if self.step == 1:
            print("release the object...")
            self.finger_release()
            self._start_timer(1000)
            self.step = 2
            return False
        
        if self.step == 2:
            self.hide_arm()
            self._start_timer(2000)
            print("Release successful")
            self.step = 3 
            return False
        
        if self.step == 3:
            self.hide_arm()
            print("--- end of loop ---")
            self.step = 0  
            return True
    def _start_timer(self, ms):
        self.timer = int(ms / 32)

    def _tick_timer(self):
        if self.timer > 0:
            self.timer -= 1
            return False
        return True