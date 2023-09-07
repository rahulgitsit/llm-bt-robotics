import py_trees as pt


class FindPlanes(pt.behaviour.Behaviour):
    def __init__(self, name, processor, planes):
        super(FindPlanes, self).__init__(name)
        self.processor = processor
        self.planes = planes
        self.blackboard = self.attach_blackboard_client()
        self.blackboard.register_key(key="plane_pos", access=pt.common.Access.WRITE)
        self.blackboard.register_key(key="in_sequence", access=pt.common.Access.WRITE)
        self.counter = 0  # should be moved to init maybe
        self.positions = dict()

    def update(self):
        if self.counter < len(self.planes):
            color, cords = self.processor.get_plane_cords(self.planes[self.counter])
            self.positions[color] = cords
            print(f"At the {self.counter + 1} plane.[{color}]")
            self.blackboard.in_sequence = False
            self.counter += 1
            return pt.common.Status.RUNNING
        else:
            self.blackboard.plane_pos = self.positions
            print("All planes covered")
            return pt.common.Status.SUCCESS


class SearchObject(pt.behaviour.Behaviour):
    def __init__(self, name, processor, colors=None, stack_loc=None):
        super(SearchObject, self).__init__(name)
        self.processor = processor
        self.blackboard = self.attach_blackboard_client()
        self.blackboard.register_key(key="plane_pos", access=pt.common.Access.READ)  # To store the position of planes
        self.blackboard.register_key(key="in_sequence",
                                     access=pt.common.Access.WRITE)  # To find colours in the order given
        self.blackboard.register_key(key="color_order",
                                     access=pt.common.Access.WRITE)  # To get the colour order for the stack
        self.blackboard.register_key(key="current_color_pos", access=pt.common.Access.WRITE)
        # self.blackboard.register_key(key="target_pos", access=pt.common.Access.WRITE) #To store the destination positon
        self.blackboard.register_key(key="color_pos_dict",
                                     access=pt.common.Access.WRITE)  # To keep track of all the cubes and its positions

        self.colors = colors
        self.stack_loc = stack_loc
        self.color_counter = 0
        self.pos_adjust = 0
        self.color_pos_dict = dict(red=set(), green=set(), blue=set())

    def update(self):
        if self.colors is not None:
            if isinstance(self.colors, list) and len(self.colors) > 1:  #stack order is given
                self.blackboard.in_sequence = True  # TODO FOR TRIAL
                search_colors = self.colors
                self.blackboard.color_order = search_colors
                if self.color_counter >= len(search_colors): #TODO might have to rethink here!!!!
                    return pt.common.Status.FAILURE #stacking is finished

                search_colors = search_colors[self.color_counter] #get the first colour
                search_colors = [search_colors]
            else: #single colour is given to pick
                print(f"Single colour search {self.colors}")
                self.blackboard.in_sequence = False  # TODO FOR TRIAL
                if not isinstance(self.colors, list):
                    search_colors = [self.colors]
                try:
                    self.blackboard.color_order.append(search_colors)
                except:
                    self.blackboard.color_order = search_colors

        else: # if not in sequence is given, it is for sorting. lazy coding
            search_colors = list(
                self.blackboard.plane_pos.keys())
            self.blackboard.in_sequence = False  # TODO FOR TRAIL

            # search_colors = self.blackboard.color_order #in sequence, make tower
        # if self.color_counter >= len(search_colors): TODO TAKE CARE OF THIS PART URGENT!!!!!!!!!
        #     return pt.common.Status.SUCCESS
        # search_colors = search_colors[self.color_counter]
        # search_colors = [search_colors]

        color, pos = self.processor.search_for_object(search_colors)  # current color and pos
        print("return from search obj:", color, pos)

        if color and pos:
            self.pos_adjust += 1  # to get the robot's arm to align correctly.
            if self.pos_adjust == 3:
                self.pos_adjust = 0
                print("SUCCESS")
                self.blackboard.current_color_pos = color, pos # storing incase the command is to just sort
                self.color_pos_dict[color].add(tuple(pos))  # store the position of all the colors and objects detected
                self.blackboard.color_pos_dict = self.color_pos_dict
                print("color and pos dictionary: ", self.blackboard.color_pos_dict.items())
                self.color_counter += 1
                if self.color_counter == 1 and self.stack_loc is None: #if stack on the search space
                    return pt.common.Status.RUNNING
                return pt.common.Status.SUCCESS
            else:
                return pt.common.Status.RUNNING
        else:
            return pt.common.Status.RUNNING


class PickUpCube(pt.behaviour.Behaviour):
    def __init__(self, name, processor, colors=None,
                 pickup_loc=None):  # TODO do we need this pick_up location here?
        super(PickUpCube, self).__init__(name)
        self.processor = processor
        self.pickup_loc = pickup_loc
        self.colors = colors
        self.blackboard = self.attach_blackboard_client()
        self.blackboard.register_key(key="color_order",
                                     access=pt.common.Access.READ)  # TODO from get tower order//MAYBE REWORK REQUIRED
        self.blackboard.register_key(key="in_sequence",
                                    access=pt.common.Access.READ)
        self.blackboard.register_key(key="current_color_pos", access=pt.common.Access.READ)
        self.blackboard.register_key(key="picked_up", access=pt.common.Access.WRITE)
        self.blackboard.register_key(key="color_pos_dict",
                                     access=pt.common.Access.WRITE)  # To keep track of all the cubes and its positions
        self.blackboard.register_key(key="pickup_history",
                                     access=pt.common.Access.WRITE)  # to keep track of the objects the arm has picked up in the past

        try:
            self.blackboard.picked_up
        except:
            self.blackboard.picked_up = False

    def update(self):
        # tower_size = len(self.blackboard.color_order) #do we need this here?
        if not self.blackboard.picked_up:
            color, pos = self.blackboard.current_color_pos
            return self.try_pickup(pos, color)
        else:
            print("Pickup not possible")
            return pt.common.Status.FAILURE

    def try_pickup(self, pos, color):
        if self.processor.pick_up(pos):
            print(f"Picking up {color} cube at {pos}")
            try:
                self.blackboard.pickup_history.append(color)  # To keep track of the cubes which have been picked up
            except:
                self.blackboard.pickup_history = [color]
            self.blackboard.picked_up=True
            return pt.common.Status.SUCCESS
        else:
            return pt.common.Status.RUNNING


class PlaceCube(pt.behaviour.Behaviour):
    def __init__(self, name, processor, target_loc=None,
                 target_color=None):  # target_loc can be any pos, keep it generic
        super(PlaceCube, self).__init__(name)
        self.processor = processor
        self.target_loc = target_loc
        self.target_color = target_color
        self.blackboard = self.attach_blackboard_client()
        self.blackboard.register_key(key="plane_pos", access=pt.common.Access.READ)  # To store the position of planes
        self.blackboard.register_key(key="in_sequence",
                                     access=pt.common.Access.READ)
        self.blackboard.register_key(key="color_order", access=pt.common.Access.READ)
        self.blackboard.register_key(key="current_color_pos", access=pt.common.Access.READ)
        self.blackboard.register_key(key="picked_up", access=pt.common.Access.WRITE)
        self.blackboard.register_key(key="color_pos_dict",
                                     access=pt.common.Access.WRITE)  # To keep track of all the cubes and its positions
        self.blackboard.register_key(key="pickup_history", access=pt.common.Access.WRITE)  # TODO NOT BEING USED
        # to keep track of the objects the arm has picked up in the past

    def update(self):
        if self.blackboard.picked_up:
            self.blackboard.picked_up = False
            picked_items = self.blackboard.pickup_history
            if self.target_loc is None and not self.blackboard.in_sequence:  # put it on the plane for sorting
                color, pos = self.blackboard.current_color_pos
                plane_pos = self.blackboard.plane_pos
                print(f"target plane {color} pos ", plane_pos[color])
                self.blackboard.color_pos_dict[color].remove(tuple(pos))
                self.blackboard.color_pos_dict[color].add(
                    tuple(plane_pos[color]))  # update the position of the cube to that of plane pos, careful about z axis
                self.processor.place_cube(plane_pos[color],picked_items.count(color))
                return pt.common.Status.SUCCESS
            elif self.target_loc is None and self.blackboard.in_sequence: #for stacking on the search space
                target_color = self.blackboard.color_order
                target_pos = self.blackboard.color_pos_dict[target_color[0]]
                target_pos = list(next(iter(target_pos)))
                self.processor.place_cube(target_pos, 1+len(picked_items))
                picked_color = picked_items[-1]
                self.blackboard.color_pos_dict[picked_color].pop()
                self.blackboard.color_pos_dict[picked_color].add(tuple(target_pos))
                return pt.common.Status.SUCCESS

            elif self.target_loc: #for stacking on a location
                self.processor.place_cube(self.target_loc, len(picked_items))
                return pt.common.Status.SUCCESS

            else: #random pos
                random_pos = [1.55, 0.77, 0.3, 0, 0, 0, 1]
                self.processor.place_cube(random_pos)
                return pt.common.Status.SUCCESS


                # NEED TO UPDATE THE LOCATIONS OF CUBES AFTER PLACING


class StackCubes(pt.behaviour.Behaviour):
    def __init__(self, name, processor, destination_plane=None, place_object=True):
        super(StackCubes, self).__init__(name)
        self.processor = processor
        self.destination_plane = destination_plane
        self.blackboard = self.attach_blackboard_client()
        self.blackboard.register_key(key="target_pos", access=pt.common.Access.READ)
        self.blackboard.register_key(key="color_order", access=pt.common.Access.READ)
        self.blackboard.register_key(key="current_color_pos", access=pt.common.Access.READ)

        if self.destination_plane is None:
            self.counter = 2
        else:
            self.counter = 1
        self.tower_size = 0
        self.place_object = place_object

    def update(self):
        self.tower_size = len(self.blackboard.color_order)
        color, pos = self.blackboard.current_color_pos
        print(f"Picking up {color} cube")
        if self.counter <= self.tower_size:
            if self.destination_plane is not None or not self.place_object:
                self.processor.build_tower(self.destination_plane, self.counter, self.place_object)
            else:
                target_pos = self.blackboard.target_pos
                self.processor.build_tower(target_pos, self.counter, self.place_object)
            self.counter += 1
            return pt.common.Status.SUCCESS
        else:
            return pt.common.Status.FAILURE
