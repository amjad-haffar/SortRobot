class RobotMovement:
    def __init__(self, robot):
        self.robot = robot
        self.timestep = int(robot.getBasicTimeStep())
        #wheels
        self.frontR=self.initWheel("wheel1")
        self.frontL=self.initWheel("wheel2")
        self.backR=self.initWheel("wheel3")
        self.backL=self.initWheel("wheel4")
        self.wheels = [self.frontR, self.frontL, self.backR, self.backL]
        self.MAX_SPEED = min(w.getMaxVelocity() for w in self.wheels)
    def initWheel(self,name):
        wheel=self.robot.getDevice(name)
        wheel.setPosition(float('inf')) 
        wheel.setVelocity(0)
        # wheel.setAvailableTorque(7.0)
        return wheel
    def rotateLeft(self,speed= None):
        if speed is None:
            speed = 0.3 * self.MAX_SPEED
        self.frontR.setVelocity(+speed)
        self.backR.setVelocity(+speed)
        self.frontL.setVelocity(-speed)
        self.backL.setVelocity(-speed)
    
    def rotateRight(self,speed= None):
        if speed is None:
            speed = 0.3 * self.MAX_SPEED
        self.frontR.setVelocity(-speed)
        self.backR.setVelocity(-speed)
        self.frontL.setVelocity(+speed)
        self.backL.setVelocity(+speed)
        
    def goLeft(self,speed= None):
        if speed is None:
            speed = 0.2 * self.MAX_SPEED
        self.frontR.setVelocity(+speed)
        self.backR.setVelocity(-speed)
        self.frontL.setVelocity(-speed)
        self.backL.setVelocity(+speed)

    def goRight(self,speed= None):
        if speed is None:
            speed = 0.2 * self.MAX_SPEED
        self.frontR.setVelocity(-speed)
        self.backR.setVelocity(+speed)
        self.frontL.setVelocity(+speed)
        self.backL.setVelocity(-speed)
        
    def forward(self,speed= None):
        if speed is None:
            speed = 0.3 * self.MAX_SPEED
        self.frontR.setVelocity(+speed)
        self.backR.setVelocity(+speed)
        self.frontL.setVelocity(+speed)
        self.backL.setVelocity(+speed)
        
    def backward(self,speed= None):
        if speed is None:
            speed = 0.3 * self.MAX_SPEED
        self.frontR.setVelocity(-speed)
        self.backR.setVelocity(-speed)
        self.frontL.setVelocity(-speed)
        self.backL.setVelocity(-speed)
        
    def stop(self):
        self.frontR.setVelocity(0)
        self.backR.setVelocity(0)
        self.frontL.setVelocity(0)
        self.backL.setVelocity(0)
