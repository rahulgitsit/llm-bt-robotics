
class SaveState:
    def __init__(self):
        self.state = dict(plane_pos="", in_sequence="", color_order=[], current_color_pos="", color_pos_dict="",
                          picked_up="",) # pickup_history=""
        # self.children = children

        # self.update_state(children)

    def update_state(self, children):
        if children is not None:
            keys = list(self.state.keys())
            for child in children:
                blackboard = child.blackboard
                for key in keys:
                    try:
                        self.state[key] = blackboard.get(key)
                    except:
                        pass
        return None

    def restore_state(self, new_children):
        if new_children is not None:
            keys = list(self.state.keys())
            for child in new_children:
                blackboard = child.blackboard
                for key in keys:
                    # if blackboard.exists(key):
                    try:
                        blackboard.set(key, self.state[key])
                    except:
                        pass
        return None

    def print_state(self):
        for key, value in self.state.items():
            print(f"key: {key} --> {value}")
