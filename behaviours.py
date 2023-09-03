import py_trees as pt

#behaviour for - sort by colour, place cube by colour,etc
class MoveToPlane(pt.behaviour.Behaviour):
    def __init__(self, name, planes, processor):
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
            color, cords = self.processor.get_plane_cords(self.planes[self.counter])
            self.positions[color] = cords
            print(f"At the {self.counter + 1} plane.[{color}]")
            self.blackboard.in_sequence=False
            self.counter += 1
            return pt.common.Status.RUNNING
        else:
            self.blackboard.plane_pos = self.positions
            print("All planes covered")
            return pt.common.Status.SUCCESS

#behaviour for - searching object by colour
class SearchObject(pt.behaviour.Behaviour):
    def __init__(self, name, processor):
        super(SearchObject, self).__init__(name)
        self.processor = processor
        self.blackboard = self.attach_blackboard_client()
        self.color_counter = 0
        self.blackboard.register_key(key="plane_pos", access=pt.common.Access.READ)
        self.blackboard.register_key(key="in_sequence", access=pt.common.Access.READ)
        self.blackboard.register_key(key="color_order", access=pt.common.Access.READ)
        self.blackboard.register_key(key="current_color_pos", access=pt.common.Access.WRITE)
        self.reset_start_pos = True
        self.pos_adjust = 0

        # self.start_location = start_location


    def update(self):
        if not self.blackboard.in_sequence:
            colors = list(self.blackboard.plane_pos.keys())
        else:
            colors = self.blackboard.color_order
            if self.color_counter>=len(colors):
                return pt.common.Status.SUCCESS
            colors = colors[self.color_counter]
            colors = [colors]
        # color, pos = self.processor.search_object(self.search_start_pos, colors)
        color, pos = self.processor.search_for_object(colors) #tryout
        print("return from search obj:", color, pos)
        self.blackboard.current_color_pos = (color, pos)
        if color and pos:
            self.pos_adjust+=1
            if self.pos_adjust == 3:
                self.pos_adjust = 0
                print("SUCCESS")
                self.color_counter+=1
                return pt.common.Status.SUCCESS
            else:
                return pt.common.Status.RUNNING
        else:
            return pt.common.Status.RUNNING

#behaviours for pick and place
class PickAndPlace(pt.behaviour.Behaviour):
    def __init__(self, name, processor):
        super(PickAndPlace, self).__init__(name)
        self.processor = processor
        self.blackboard = self.attach_blackboard_client()
        self.blackboard.register_key(key="plane_pos", access=pt.common.Access.READ)
        self.blackboard.register_key(key="current_color_pos", access=pt.common.Access.READ)
        self.blackboard.register_key(key="in_sequence", access=pt.common.Access.READ)


    def update(self):
        color, pos = self.blackboard.current_color_pos
        plane_pos = self.blackboard.plane_pos
        print("target plane pos " ,plane_pos[color])
        self.processor.pick_and_place(pos, color, plane_pos)
        return pt.common.Status.SUCCESS

class GetTowerOrder(pt.behaviour.Behaviour):
    def __init__(self, name, processor):
        super(GetTowerOrder, self).__init__(name)
        self.processor = processor
        self.input_read = False
        self.blackboard = self.attach_blackboard_client()
        self.blackboard.register_key(key="tower_pos", access=pt.common.Access.WRITE)
        self.blackboard.register_key(key="in_sequence", access=pt.common.Access.WRITE)
        self.blackboard.register_key(key="color_order",access=pt.common.Access.WRITE)
        self.color_names = {
            'R': 'red',
            'G': 'green',
            'B': 'blue'
        }

    def update(self):
        if not self.input_read:
            color_code = input("Enter the colour order for the tower (e.g. 'RBGR')")
            colors = [self.color_names[char] for char in color_code]
            self.blackboard.in_sequence=True
            self.input_read=True
            self.blackboard.color_order = colors
        return pt.common.Status.SUCCESS

class MakeTower(pt.behaviour.Behaviour):
    def __init__(self, name, processor, destination_plane):
        super(MakeTower, self).__init__(name)
        self.processor = processor
        self.destination_plane = destination_plane
        self.blackboard = self.attach_blackboard_client()
        self.blackboard.register_key(key="color_order",access=pt.common.Access.READ)
        self.blackboard.register_key(key="current_color_pos",access=pt.common.Access.READ)
        self.counter = 1
        self.tower_size = 0

    def update(self):
        self.tower_size = len(self.blackboard.color_order)
        color, pos = self.blackboard.current_color_pos
        print(f"Picking up {color} cube")
        if self.counter <= self.tower_size:
            self.processor.build_tower(self.destination_plane, self.counter)
            self.counter+=1
            return pt.common.Status.SUCCESS
        else:
            return pt.common.Status.FAILURE