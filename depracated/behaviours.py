import py_trees as pt


# behaviour for - sort by colour, place cube by colour,etc
class MoveToPlane(pt.behaviour.Behaviour):
    def __init__(self, name, processor, planes):
        super(MoveToPlane, self).__init__(name)
        self.processor = processor
        self.planes = planes
        self.blackboard = self.attach_blackboard_client()
        self.blackboard.register_key(key="plane_pos", access=pt.common.Access.WRITE)
        self.blackboard.register_key(key="in_sequence", access=pt.common.Access.WRITE)
        self.counter = 0  # should be moved to init maybe
        self.positions = dict()

    def update(self):
        if self.counter < len(self.planes):
            color, cords = self.processor.get_plane_coordinates(self.planes[self.counter])
            self.positions[color] = cords
            print(f"At the {self.counter + 1} plane.[{color}]")
            self.blackboard.in_sequence = False
            self.counter += 1
            return pt.common.Status.RUNNING
        else:
            self.blackboard.plane_pos = self.positions
            print("All planes covered")
            return pt.common.Status.SUCCESS


# behaviour for - searching object by colour
class SearchObject(pt.behaviour.Behaviour):
    def __init__(self, name, processor, colors=None, store_pos=False):
        super(SearchObject, self).__init__(name)
        self.processor = processor
        self.blackboard = self.attach_blackboard_client()
        self.blackboard.register_key(key="plane_pos", access=pt.common.Access.READ)
        self.blackboard.register_key(key="in_sequence", access=pt.common.Access.READ)
        self.blackboard.register_key(key="color_order", access=pt.common.Access.WRITE)
        self.blackboard.register_key(key="current_color_pos", access=pt.common.Access.WRITE)
        self.blackboard.register_key(key="target_pos", access=pt.common.Access.WRITE)

        self.colors = colors
        self.store_pos = store_pos
        self.color_counter = 0
        self.pos_adjust = 0

    def update(self):
        if self.colors is not None:
            search_colors = self.colors
            search_colors = [search_colors]
            try:
                self.blackboard.color_order.append(search_colors)
            except:
                self.blackboard.color_order = search_colors
        elif not self.blackboard.in_sequence:
            search_colors = list(self.blackboard.plane_pos.keys())
        else:
            search_colors = self.blackboard.color_order
            if self.color_counter >= len(search_colors):
                return pt.common.Status.SUCCESS
            search_colors = search_colors[self.color_counter]
            search_colors = [search_colors]

        color, pos = self.processor.search_for_object(search_colors)  # tryout
        print("return from search obj:", color, pos)
        self.blackboard.current_color_pos = (color, pos)

        if color and pos:
            self.pos_adjust += 1

            if self.store_pos and pos:
                print(f"Target position {pos} stored")
                self.blackboard.target_pos = pos.copy()
            if self.pos_adjust == 3:
                self.pos_adjust = 0
                print("SUCCESS")
                self.color_counter += 1
                return pt.common.Status.SUCCESS
            else:
                return pt.common.Status.RUNNING
        else:
            return pt.common.Status.RUNNING


# behaviours for pick and place
class PickAndPlace(pt.behaviour.Behaviour):
    def __init__(self, name, processor, ):
        super(PickAndPlace, self).__init__(name)
        self.processor = processor

        self.blackboard = self.attach_blackboard_client()
        self.blackboard.register_key(key="plane_pos", access=pt.common.Access.READ)
        self.blackboard.register_key(key="current_color_pos", access=pt.common.Access.READ)
        self.blackboard.register_key(key="in_sequence", access=pt.common.Access.READ)

    def update(self):
        color, pos = self.blackboard.current_color_pos
        plane_pos = self.blackboard.plane_pos
        print("target plane pos ", plane_pos[color])
        self.processor.pick_and_place(color, plane_pos)
        return pt.common.Status.SUCCESS


class GetTowerOrder(pt.behaviour.Behaviour):
    def __init__(self, name, processor, tower_color_order):
        super(GetTowerOrder, self).__init__(name)
        self.processor = processor
        self.input_read = False
        self.blackboard = self.attach_blackboard_client()
        self.blackboard.register_key(key="tower_pos", access=pt.common.Access.WRITE)
        self.blackboard.register_key(key="in_sequence", access=pt.common.Access.WRITE)
        self.blackboard.register_key(key="color_order", access=pt.common.Access.WRITE)
        self.color_names = {
            'R': 'red',
            'G': 'green',
            'B': 'blue'
        }
        self.tower_color_order = tower_color_order
        self.tower_color_order = self.tower_color_order.upper()

    def update(self):
        if not self.input_read:
            # color_code = input("Enter the colour order for the tower (e.g. 'RBGR')")
            if not all(char in 'RGB' for char in self.tower_color_order):
                print("The string contains characters other than 'R', 'G', and 'B'.")
                return pt.common.Status.FAILURE

            colors = [self.color_names[char] for char in self.tower_color_order]
            self.blackboard.in_sequence = True
            self.input_read = True
            self.blackboard.color_order = colors
        return pt.common.Status.SUCCESS


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
