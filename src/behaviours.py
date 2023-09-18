import random

import py_trees as pt


def handle_errors():
    pass


class FindPlanes(pt.behaviour.Behaviour):
    """
    Finds and tracks specific planes in the environment.

    Attributes:
        name (str): Behavior name.
        processor: Data processing module.
        planes (list): List of target plane identifiers.
        colors (list, optional): Expected plane colors.

    Methods:
        update(self):
            Executes the behavior, finding and tracking planes.

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
        Update Method for Finding Planes

        Executes the process of locating and tracking specific planes.

        :returns:
            SUCCESS: Target plane found.
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


class SearchCubeOrder(pt.behaviour.Behaviour):
    """
    Searches for and tracks cubes of specified colors in the scene.

    Attributes:
        name (str): Behavior name.
        processor: Data processing module.
        colors (list/str): List of target colors, 'plane_colors', or 'random'.
        stack_loc (str, optional): Location for stacking objects.

    Methods:
        update(self):
            Executes the behavior, searching for and tracking cubes.

        search_until_alignment(self, color, position):
            Continues searching until the arm's position is aligned.

    """

    def __init__(self, name, processor, stack_color_order=None, stack_loc=None):
        super(SearchCubeOrder, self).__init__(name)
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
        self.blackboard.register_key(key="stack_locations", access=pt.common.Access.WRITE)

        self.blackboard.stack_locations = []

        self.colors = stack_color_order
        self.stack_loc = stack_loc
        self._color_counter = 0
        self._pos_adjust = 0
        self._color_pos_dict = dict(red=set(), green=set(), blue=set())
        self._search_space_stack_loc = None
        self._exclude_pos = None
        self._search_counter = 0

    def update(self):
        """
        Update Method for Searching cubes

        Executes the process of searching for and tracking cubes of specified colors.

        :returns:
            SUCCESS: cubes found and aligned.
            RUNNING: Behavior still in progress.
            FAILURE: Unable to find the object or found all requested cubes.
        """

        if isinstance(self.colors, list):
            if len(self.colors) > 1:  # stack order is given
                self.blackboard.in_sequence = True
                self.blackboard.color_order = self.colors
                if self._color_counter >= len(self.colors):
                    return pt.common.Status.FAILURE  # nothing left to stack

                search_colors = [self.colors[self._color_counter]]  # get the first colour
            else:  # single colour is given to pick
                print(f"Single colour search {self.colors}")
                self.blackboard.in_sequence = False
                search_colors = self.colors
                self.blackboard.color_order = search_colors

        elif self.colors == "plane_colors":
            search_colors = list(self.blackboard.plane_pos.keys())
            self.blackboard.in_sequence = False

        elif self.colors == "random":
            search_colors = random.sample(["red", "blue", "green"])

        else:
            raise ValueError("Invalid color!")

        color, position = self.processor.search_for_object(search_colors,
                                                           self._exclude_pos)  # current color and position
        self._search_counter += 1

        print(f"Detected colour: {color} @ position: {position}")

        if self._search_counter > 15:
            return pt.common.Status.FAILURE

        if color and position:
            return self.search_until_alignment(color, position)

        return pt.common.Status.RUNNING

    def search_until_alignment(self, color, position):
        """
        Alignment and Object Tracking Method

        Continues searching until the arm's position is aligned with the cube's position.

        Args:
            color (str): Detected cube's color.
            position (tuple): Detected object's position.

        :returns
            SUCCESS: Object found and aligned, or stacking completed.
            RUNNING: Behavior still in progress.
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

            if self._color_counter == 1 and self.stack_loc is not None and "cube" in self.stack_loc:
                self._exclude_pos = position.copy()  # if stack on the search space, exclude that pos from search
                self.blackboard.stack_locations.append(position.copy())
                return pt.common.Status.RUNNING
            return pt.common.Status.SUCCESS
        return pt.common.Status.RUNNING


class PickUpCube(pt.behaviour.Behaviour):
    """
    PickUpCube Behavior

    This behavior is responsible for picking up cubes of specified colors.

    Attributes:
        name (str): Behavior name.
        processor: Data processing module.

    Methods:
        update(self):
            Executes the process of picking up cubes.

        try_pickup(self, pos, color):
            Attempts to pick up a cube at a given position.
    """

    def __init__(self, name, processor):
        super(PickUpCube, self).__init__(name)
        self.processor = processor
        # self.colors = colors
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

        self.blackboard.pickup_history = []
        self.blackboard.picked_up = False

    def update(self):
        """
        Update Method for Picking Up Cubes

        Executes the process of attempting to pick up cubes.

        :returns:
            SUCCESS: Cube successfully picked up.
            RUNNING: Pickup attempt still in progress.
            FAILURE: Unable to pick up the cube.
        """
        if not self.blackboard.picked_up:
            color, pos = self.blackboard.current_color_pos
            return self.try_pickup(pos, color)
        else:
            print("Pickup not possible. Suction pad busy!")
            return pt.common.Status.FAILURE

    def try_pickup(self, pos, color):
        """
        try_pickup Method

        Attempts to pick up a cube at a given position.

        Args:
            pos (tuple): Position of the cube to be picked up.
            color (str): Color of the cube to be picked up.

        :returns:
            SUCCESS: Cube successfully picked up.
            RUNNING: Pickup attempt still in progress.
            FAILURE: Unable to pick up the cube.
        """
        if self.processor.pick_up(pos):
            print(f"Picking up {color} cube at {pos}")
            self.blackboard.pickup_history.append(color)  # To keep track of the cubes which have been picked up
            self.blackboard.picked_up = True

            print(f"Pickup history --> [{self.blackboard.pickup_history}]")
            return pt.common.Status.SUCCESS
        else:
            return pt.common.Status.RUNNING


class PlaceCube(pt.behaviour.Behaviour):
    """
    This behavior is responsible for placing cubes in specified locations.

    Attributes:
        name (str): Behavior name.
        processor: Data processing module.
        target_loc (str/tuple, optional): Target location for placing cubes.

    Methods:
        update(self):
            Executes the process of placing cubes in specified locations.

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
        """
        Update Method for Placing Cubes

        Executes the process of placing cubes in specified locations.

        :returns:
            SUCCESS: Cube successfully placed.
            FAILURE: Unable to place the cube.
        """
        if not self.blackboard.picked_up:
            return pt.common.Status.FAILURE

        self.blackboard.picked_up = False
        picked_items = self.blackboard.pickup_history

        if isinstance(self.target_loc, str):
            if self.target_loc == "sort_planes":  # put it on the plane for sorting
                color, pos = self.blackboard.current_color_pos
                try:
                    plane_pos = self.blackboard.plane_pos
                except KeyError:
                    plane_pos = pos
                    self.processor.place_cube(plane_pos, picked_items.count(color))
                    return pt.common.Status.FAILURE

                print(f"target plane: {color} pos {plane_pos[color]}")
                self.blackboard.color_pos_dict[color].remove(tuple(pos))
                # update the position of the cube to that of plane pos, careful about z axis
                self.blackboard.color_pos_dict[color].add(tuple(plane_pos[color]))
                self.processor.place_cube(plane_pos[color], picked_items.count(color))
                return pt.common.Status.SUCCESS

            elif "cube" in self.target_loc and self.blackboard.in_sequence:  # for stacking on the search space
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

            elif self.target_loc in ["red_plane", "blue_plane", "green_plane"]:
                plane_pos = self.blackboard.plane_pos[self.target_loc[:-6]]
                self.processor.place_cube(plane_pos, len(picked_items))
                return pt.common.Status.SUCCESS

        elif isinstance(self.target_loc, int):
            try:
                self.processor.place_cube(self.target_loc, len(picked_items))  # allotted plane is int
                return pt.common.Status.SUCCESS
            except AttributeError:
                print("Invalid inputs! Placing the object failed")
                return pt.common.Status.FAILURE
        else:
            return pt.common.Status.FAILURE