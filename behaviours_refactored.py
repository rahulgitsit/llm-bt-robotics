import py_trees as pt


class FindPlanes(pt.behaviour.Behaviour):
    """
    Behavior class for finding and tracking planes where the cubes will be sorted.

    Args:
        name (str): The name of the behavior.
        processor (Processor): An instance of the processor class.
        planes (list): A list of planes where the cubes need to be stacked.
        colors (str): The color of the plane where the cube needs to be stacked.

    Attributes:
        processor (Processor): The processor class instance.
        planes (list): The list of planes to be tracked.
        blackboard (Blackboard): The blackboard for communication within the tree,
        counter (int): Keeps track of the number of planes processed.
        positions (dict): Stores positions of tracked planes.

    """

    def __init__(self, name, processor, planes, colors=None):
        super(FindPlanes, self).__init__(name)
        self._plane_found = False
        self.processor = processor
        self.planes = planes
        self.blackboard = self.attach_blackboard_client(name="FindPlanesClient")
        self.blackboard.register_key(key="plane_pos", access=pt.common.Access.WRITE)
        self.blackboard.register_key(key="in_sequence", access=pt.common.Access.WRITE)
        self.counter = 0
        self.positions = dict()
        self.plane_color = colors

    def update(self):
        """
        Update method to find and track planes.

        Returns:
            pt.common.Status: The current status of the behavior.
        """
        if self._plane_found:
            return pt.common.Status.SUCCESS

        elif self.counter < len(self.planes):
            color, cords = self.processor.get_plane_coordinates(self.planes[self.counter])
            self.positions[color] = cords
            print(f"At the {self.counter + 1} plane.[{color}]")
            self.blackboard.in_sequence = False
            self.counter += 1
            if self.plane_color and self.plane_color == color:
                self._plane_found = True
                self.blackboard.plane_pos = self.positions
                return pt.common.Status.SUCCESS

            return pt.common.Status.RUNNING
        else:
            self.blackboard.plane_pos = self.positions
            print("All planes covered")
            return pt.common.Status.SUCCESS


class SearchObject(pt.behaviour.Behaviour):
    """
       A behavior class for searching and processing blobs based on their colors.

       Args:
           name (str): The name of the behavior.
           processor: An instance of the processor class.
           colors (list or str, optional): A list of colors to search for or a single color string.
               If provided, the behavior will search for objects of specific colors in the specified order.
               Defaults to None.
           stack_loc: The location to stack the objects once found. Defaults to None.

       Attributes:
           blackboard: An instance of a blackboard client for communication with the behavior tree.
           colors: The list of colors to search for or a single color string.
           stack_loc: The location to stack the objects.
           _color_counter (int): Internal counter to count the no. of colors searched from list of colors provided.
           _pos_adjust (int): Internal adjustment value for object positions.
           _color_pos_dict (dict): A dictionary to keep track of all detected cubes and their positions.
           _search_space_stack_loc: The location to search for stacking objects.
           _exclude_pos: Positions to exclude during the search.
           _search_counter (int): Internal counter for the number of search attempts.

       Methods:
           update(self):
               Executes the behavior logic for searching and processing objects.
               Returns a behavior tree status code (pt.common.Status).
    """
    def __init__(self, name, processor, colors=None, stack_loc=None):
        super(SearchObject, self).__init__(name)
        self.processor = processor
        self.blackboard = self.attach_blackboard_client(name="SearchClient")
        self.blackboard.register_key(key="plane_pos", access=pt.common.Access.READ)  # To store the position of planes
        self.blackboard.register_key(key="in_sequence",
                                     access=pt.common.Access.WRITE)  # To find colours in the order given
        self.blackboard.register_key(key="color_order",
                                     access=pt.common.Access.WRITE)  # To get the colour order for the stack
        self.blackboard.register_key(key="current_color_pos", access=pt.common.Access.WRITE)
        self.blackboard.register_key(key="color_pos_dict",
                                     access=pt.common.Access.WRITE)  # To keep track of all the cubes and its positions

        self.colors = colors
        self.stack_loc = stack_loc
        self._color_counter = 0
        self._pos_adjust = 0
        self._color_pos_dict = dict(red=set(), green=set(), blue=set())
        self._search_space_stack_loc = None
        self._exclude_pos = None
        self._search_counter = 0

    def update(self):
        """
               Executes the behavior logic for searching and processing objects.

               Returns:
                   pt.common.Status: The behavior tree status code indicating SUCCESS, FAILURE, or RUNNING.
       """
        if self.colors is not None:
            if isinstance(self.colors, list) and len(self.colors) > 1:  # stack order is given
                self.blackboard.in_sequence = True
                self.blackboard.color_order = self.colors
                if self._color_counter >= len(self.colors):  # TODO might have to rethink here!!!!
                    return pt.common.Status.FAILURE  # nothing left to stack

                search_colors = [self.colors[self._color_counter]]  # get the first colour
            else:  # single colour is given to pick
                print(f"Single colour search {self.colors}")
                self.blackboard.in_sequence = False
                search_colors = [self.colors] if isinstance(self.colors, str) else self.colors
                self.blackboard.color_order = search_colors

        else:  # TODO sorting condition here is implicitly known, maybe need to be reworked during chat feedback part
            search_colors = list(self.blackboard.plane_pos.keys())
            self.blackboard.in_sequence = False

        color, position = self.processor.search_for_object(search_colors, self._exclude_pos)  # current color and position
        self._search_counter += 1

        print(f"Detected colour: {color} @ position: {position}")

        if self._search_counter > 15:
            return pt.common.Status.FAILURE

        if color and position:
            return self.search_until_alignment(color, position)

        return pt.common.Status.RUNNING

    def search_until_alignment(self, color, position):
        """
           Continuously searches for objects until the arm's position is aligned with the detected object's position.

           Args:
               color (str): The color of the detected object.
               position (tuple): The position of the detected object.

           Returns:
               pt.common.Status: The behavior tree status code indicating SUCCESS, FAILURE, or RUNNING.
           """
        self._pos_adjust += 1
        self._search_counter = 0

        if self._pos_adjust == 3:
            self._pos_adjust = 0
            print("Arm position aligned.")
            self.blackboard.current_color_pos = color, position
            self._color_pos_dict[color].add(
                tuple(position))  # store the position of all the colors and objects detected
            self.blackboard.color_pos_dict = self._color_pos_dict
            print("Color and position dictionary: ", self.blackboard.color_pos_dict.items())
            self._color_counter += 1

            if self._color_counter == 1 and "cube" in self.stack_loc and len(self.blackboard.color_order) > 1:  # if stack on the search space
                self._exclude_pos = position.copy()
                return pt.common.Status.RUNNING
            return pt.common.Status.SUCCESS
        return pt.common.Status.RUNNING


class PickUpCube(pt.behaviour.Behaviour):
    """
       A behavior class for picking up cubes based on their color.

       Args:
           name (str): The name of the behavior.
           processor: An instance of the processor class.
           colors (list or str, optional): A list of colors to pick up or a single color string.
               Defaults to None.

       Attributes:
           colors: The list of colors to pick up or a single color string.
           blackboard: An instance of a blackboard client for communication with the behavior tree.
               It registers keys for accessing information from other behaviors.
           blackboard.picked_up (bool): A flag indicating whether a cube has been successfully picked up.
           blackboard.pickup_history (list): A list to keep track of the colors of cubes picked up.

       Methods:
           update(self):
               Executes the behavior logic for picking up cubes.
               Returns a behavior tree status code (pt.common.Status).

           try_pickup(self, pos, color):
               Attempts to pick up a cube at the specified position.
"""
    def __init__(self, name, processor, colors=None):
        super(PickUpCube, self).__init__(name)
        self.processor = processor
        self.colors = colors
        self.blackboard = self.attach_blackboard_client(name="PickUpClient")
        self.blackboard.register_key(key="color_order",
                                     access=pt.common.Access.READ)
        self.blackboard.register_key(key="in_sequence",
                                     access=pt.common.Access.READ)
        self.blackboard.register_key(key="current_color_pos", access=pt.common.Access.READ)
        self.blackboard.register_key(key="picked_up", access=pt.common.Access.WRITE)
        self.blackboard.register_key(key="_color_pos_dict",
                                     access=pt.common.Access.WRITE)  # To keep track of all the cubes and its positions
        self.blackboard.register_key(key="pickup_history",
                                     access=pt.common.Access.WRITE)  # to keep track of the objects the arm has picked up in the past

        try:
            self.blackboard.picked_up
        except:
            self.blackboard.picked_up = False

    def update(self):
        """
                Executes the behavior logic for picking up cubes.

                Returns:
                    pt.common.Status: The behavior tree status code indicating SUCCESS, FAILURE, or RUNNING.
        """
        if not self.blackboard.picked_up:
            color, pos = self.blackboard.current_color_pos
            return self.try_pickup(pos, color)
        else:
            print("Pickup not possible. Suction pad busy!")
            return pt.common.Status.FAILURE

    def try_pickup(self, pos, color):
        """
                Attempts to pick up a cube at the specified position.

                Args:
                    pos (tuple): The position of the cube to pick up.
                    color (str): The color of the cube to pick up.

                Returns:
                    pt.common.Status: The behavior tree status code indicating SUCCESS, FAILURE, or RUNNING.
        """
        if self.processor.pick_up(pos):
            print(f"Picking up {color} cube at {pos}")
            try:
                self.blackboard.pickup_history.append(color)  # To keep track of the cubes which have been picked up
            except:
                self.blackboard.pickup_history = [color]
            self.blackboard.picked_up = True

            print(f"Pickup history --> [{self.blackboard.pickup_history}]")
            return pt.common.Status.SUCCESS
        else:
            return pt.common.Status.RUNNING


class PlaceCube(pt.behaviour.Behaviour):
    """
       A behavior class for placing cubes at specified locations.

       Args:
           name (str): The name of the behavior.
           processor: An object that performs the cube placement.
           target_loc: The target location for placing the cube.
               It can be a specific position, "random" for random placement,
               or one of ["red_plane", "blue_plane", "green_plane"] for placing on color-specific planes.
               Defaults to None.

       Attributes:
           processor: An object responsible for cube placement.
           target_loc: The target location for placing the cube.
           blackboard: An instance of a blackboard client for communication with the behavior tree.
               It registers keys for accessing information from other behaviors.

       Methods:
           update(self):
               Executes the behavior logic for placing cubes.
               Returns a behavior tree status code (pt.common.Status).
       """


    def __init__(self, name, processor, target_loc=None):  # target_loc can be any pos, keep it generic
        super(PlaceCube, self).__init__(name)
        self.processor = processor
        self.target_loc = target_loc
        self.blackboard = self.attach_blackboard_client(name="PlaceClient")
        self.blackboard.register_key(key="plane_pos", access=pt.common.Access.READ)  # To store the position of planes
        self.blackboard.register_key(key="in_sequence",
                                     access=pt.common.Access.READ)
        self.blackboard.register_key(key="color_order", access=pt.common.Access.READ)
        self.blackboard.register_key(key="current_color_pos", access=pt.common.Access.READ)
        self.blackboard.register_key(key="picked_up", access=pt.common.Access.WRITE)
        self.blackboard.register_key(key="color_pos_dict",
                                     access=pt.common.Access.WRITE)  # To keep track of all the cubes and its positions
        self.blackboard.register_key(key="pickup_history", access=pt.common.Access.WRITE)  #
        # to keep track of the objects the arm has picked up in the past

    def update(self):
        if not self.blackboard.picked_up:
            return pt.common.Status.FAILURE

        self.blackboard.picked_up = False
        picked_items = self.blackboard.pickup_history

        if self.target_loc is None and not self.blackboard.in_sequence:  # put it on the plane for sorting
            color, pos = self.blackboard.current_color_pos
            try:
                plane_pos = self.blackboard.plane_pos
            except KeyError:
                plane_pos = pos
                self.processor.place_cube(plane_pos, picked_items.count(color))
                return pt.common.Status.FAILURE

            print(f"target plane: {color} pos {plane_pos[color]}")
            self.blackboard.color_pos_dict[color].remove(tuple(pos))
            self.blackboard.color_pos_dict[color].add(
                tuple(
                    plane_pos[color]))  # update the position of the cube to that of plane pos, careful about z axis
            self.processor.place_cube(plane_pos[color], picked_items.count(color))
            return pt.common.Status.SUCCESS

        elif isinstance(self.target_loc, str):
            if "cube" in self.target_loc and self.blackboard.in_sequence: # for stacking on the search space
                target_color = self.blackboard.color_order
                target_pos = self.blackboard.color_pos_dict[target_color[0]]
                target_pos = list(next(iter(target_pos)))
                self.processor.place_cube(target_pos, 1 + len(picked_items))
                picked_color = picked_items[-1]
                self.blackboard.color_pos_dict[picked_color].pop()
                self.blackboard.color_pos_dict[picked_color].add(tuple(target_pos))
                return pt.common.Status.SUCCESS

            elif self.target_loc == "random":
                random_pos = self.processor.random_position_generator()
                self.processor.place_cube(random_pos, len(picked_items))
                return pt.common.Status.SUCCESS

            elif self.target_loc in ["red_plane","blue_plane","green_plane"]:
                plane_pos = self.blackboard.plane_pos[self.target_loc[:-6]]
                self.processor.place_cube(plane_pos, len(picked_items))
                return pt.common.Status.SUCCESS

        try:
            self.processor.place_cube(self.target_loc, len(picked_items))
            return pt.common.Status.SUCCESS
        except ValueError:
            print("Invalid inputs! Placing the object failed")
            return pt.common.Status.FAILURE
