class Sensors:
    def __init__(self, sim):
        self.sim = sim
        self.arm_vision_sensor_handle = sim.getObject('/IRB4600/blobTo3dPosition/sensor')
        self.proximity_sensor = sim.getObject('/IRB4600/suctionPad/Proximity_sensor')

    def get_proximity_sensor(self):
        return self.sim.handleProximitySensor(self.proximity_sensor)

