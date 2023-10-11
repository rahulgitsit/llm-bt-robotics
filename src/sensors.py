class Sensors:
    """
       The `Sensors` class represents the sensors used for various detection and sensing tasks.

       Attributes:
           sim: The simulation environment.
           arm_vision_sensor_handle: Handle for the arm vision sensor.
           proximity_sensor: Handle for the proximity sensor.

       Methods:
           __init__(self, sim):
               Initialises an instance of the Sensors class.

           get_proximity_sensor(self):
               Gets the readings from the proximity sensor.

   """
    def __init__(self, sim):
        """
           Initialises an instance of the Sensors class.

           Args:
               sim: The simulation environment.
       """
        self.sim = sim
        self.arm_vision_sensor_handle = sim.getObject('/IRB4600/blobTo3dPosition/sensor')
        self.proximity_sensor = sim.getObject('/IRB4600/suctionPad/Proximity_sensor')

    def get_proximity_sensor(self):
        """
            Gets the readings from the proximity sensor.

            Returns:
                tuple: A tuple containing proximity sensor readings
        """

        return self.sim.handleProximitySensor(self.proximity_sensor)

