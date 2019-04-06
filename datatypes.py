P_PLUS = "P+"
P_MIN = "P-"
I_PLUS = "I+"
I_MIN = "I-"

POINT = "point"
INTERVAL = "interval"

R_TYPES = [P_PLUS, P_MIN, I_PLUS, I_MIN]
S_TYPES = [POINT, INTERVAL]

INVERSE_MAPPING = {"-": "+", "+": "-", 0: 0}

HASHES = {}


class Entity:
    def __init__(self, name, magnitude, derivative, incoming_relations=None, outgoing_relations=None):
        self.name = name
        self.magnitude = magnitude
        self.derivative = derivative
        self.incoming_relations = incoming_relations or []# all the relations that influence this object
        self.outgoing_relations = outgoing_relations or []
        self.uuid = 0

    def calculate_transitions(self):
        derivative_list = []
        entities = []
        for r in self.incoming_relations:
            d = r.calculate_derivative()
            if not d==0:
                derivative_list.append(d)

        if len(derivative_list) == 0:
            derivative_list = [self.derivative.current.value]

        for d in set(derivative_list):
            if not self.magnitude:
                entities.append(
                    Entity(self.name,None,Derivative(self.derivative.states, d))
                )
                continue

            if d == 0:
                magnitudes = [self.magnitude.current]
            elif d == "+":
                magnitudes = self.magnitude.increase()
                if len(magnitudes)==1 and magnitudes[0] == self.magnitude.current:
                    #if there is no increase in the magnitude the derivative should be zero
                    d = 0
            else:
                magnitudes = self.magnitude.decrease()
                if len(magnitudes)==1 and magnitudes[0] == self.magnitude.current:
                    d = 0

            for m in magnitudes:
                mag = Magnitude(self.magnitude.states, m)
                der = Derivative(self.derivative.states, self.derivative.current.copy(d))
                entities.append(Entity(self.name, mag, der))

        return entities

    def get_P(self, inv=False):
        if inv:
            return INVERSE_MAPPING[self.derivative.current]
        return self.derivative.current

    def get_I(self, inv=False):
        if inv:
            return INVERSE_MAPPING[self.magnitude.get_value()]
        return self.magnitude.get_value()

    @property
    def hash(self):
        return f"{self.name}{self.magnitude.current}{self.derivative.current}"

    def copy(self):
        return Entity(self.name,self.magnitude.copy(),self.derivative.copy())

class Relation:
    def __init__(self, r_type, from_text="", to_text="", from_ent=None, to_ent=None):
        assert r_type in R_TYPES, f"{r_type} unknown"
        self.r_type = r_type
        self.from_text = from_text
        self.to_text = to_text

        self.from_ent = from_ent
        self.to_ent = to_ent

    def set_ents(self, frm, to):
        self.from_ent = frm
        self.to_ent = to

    def calculate_derivative(self):
        if self.r_type == P_PLUS:
            state = self.from_ent.get_P()
        elif self.r_type == P_MIN:
            state = self.from_ent.get_P(inv=True)
        elif self.r_type == I_PLUS:
            state = self.from_ent.get_I()
        elif self.r_type == I_MIN:
            state = self.from_ent.get_I(inv=True)
        else:
            raise Exception(f"{self.r_type}not defined")
        return state

class Dependency:
    def __init__(self,from_e,to_e,from_attr,to_attr,from_val,to_val,restriction):
        self.from_e = from_e
        self.to_e = to_e
        self.from_attr = from_attr
        self.to_attr = to_attr
        self.from_val = from_val
        self.to_val = to_val
        self.restriction = restriction# equal, different,set

    def check_dependency(self,entities):
        if self.restriction=="equal":
            f_e=entities.get(self.from_e)
            t_e=entities.get(self.to_e)
            f_val = getattr(f_e,self.from_attr)
            t_val = getattr(t_e,self.to_attr)
            if self.from_val==f_val.current:
                return self.to_val == t_val.current
            return True

        #set the value
        if self.restriction == "set":
            f_e = entities.get(self.from_e)
            t_e = entities.get(self.to_e)
            f_val = getattr(f_e, self.from_attr)
            t_val = getattr(t_e, self.to_attr)
            if self.from_val == f_val.current and t_val.current is not self.to_val:
               t_val.set_current(self.to_val)
            return True
        raise Exception("restriction unknown",self.restriction)


class Magnitude:
    def __init__(self, states, current):
        self.states = states
        if isinstance(current,str):
            print(current)
        self.current = current
        self.current_index = states.index(current)
        self.uuid = 0

    def set_current(self,val):
        self.current = self.current.copy()
        self.current.value = val
        self.current_index = self.states.index(val)


    def get_value(self):
        # todo what to do with negative magnitude?
        if self.current == 0:
            return 0
        return "+"

    @property
    def point_state(self):
        return self.current.s_type == POINT

    def increase(self):
        if self.point_state:
            return self.states[:self.current_index] or self.states[:self.current_index + 1]
        return self.states[:self.current_index + 1]

    def decrease(self):
        if self.point_state:
            return self.states[self.current_index + 1:] or self.states[self.current_index:]
        return self.states[self.current_index:]

    def copy(self):
        return Magnitude(self.states, self.current)

    def __eq__(self, other):
        if isinstance(other,Magnitude):
            return self.current.value == other.current.value
        return False

class Derivative:
    def __init__(self, states, current):
        assert current in states, f"{current} unknown"
        if not isinstance(current,State):
            print(current)
        self.states = states
        self.current = current
        self.current_index = states.index(current)
        self.uuid = 0

    def copy(self):
        return Derivative(self.states, self.current)

    def set_current(self,val):
        self.current = self.current.copy()
        self.current.value = val
        self.current_index = self.states.index(val)

class State:
    def __init__(self, s_type, value, name="", order=0):
        assert s_type in S_TYPES

        self.s_type = s_type  # point or interval
        self.value = value
        self.name = name
        self.order = order

    def __str__(self):
        return str(self.value)

    def __eq__(self, other):
        if isinstance(other, int):
            return self.value == other
        if isinstance(other, str):
            return self.value == other

        if not isinstance(other, State): return False
        return self.value == other.value and self.s_type == other.s_type

    def __hash__(self):
        return hash(self.value)

    def copy(self,val=None):
        if val is None:val=self.value
        return State(self.s_type,val,self.name,self.order)

class Network:
    counter = 0

    def __init__(self, entities, relations,dependencies):
        self.entities = entities
        self.relations = relations
        self.dependencies = dependencies
        self.root_of = {}
        self._hash = None
        self.uuid = None
        self.count = None

    def generate_spinoffs(self):
        if not self.hash in HASHES: HASHES[self.hash] = self
        entities = {}
        for ent in self.entities.values():
            entities[ent.name] = ent.calculate_transitions()

        networks = build_networks_recursively(entities, {}, self.relations,self.dependencies)

        new_networks = []
        for n in networks:
            if n.hash in HASHES:
                self.root_of[n.hash] = (HASHES[n.hash])
            elif n.hash in self.root_of:
                pass
            else:
                self.root_of[n.hash] = n
                new_networks.append(n)
                HASHES[n.hash] = n

        print(len(new_networks))
        return new_networks

    def init_count(self):
        self.count = Network.counter
        Network.counter += 1

    @property
    def hash(self):
        if self._hash is not None: return self._hash
        s = ""
        for e in sorted(self.entities.values(), key=lambda e: e.name):
            s += e.hash

        self._hash = s
        return s


def build_networks_recursively(state_space_dict, entities, relations, dependencies):
    if len(state_space_dict) > 0:
        state_space_dict = dict(state_space_dict)
        state_space = state_space_dict.popitem()[1]  # is a list
        networks = []
        for ent in state_space:
            cur_entities = dict(entities)
            e = Entity(ent.name, ent.magnitude.copy(), ent.derivative.copy())
            cur_entities[e.name] = e
            networks += build_networks_recursively(state_space_dict, cur_entities, relations,dependencies)
        return networks

    cur_relations = []
    current_ents = {}
    for key,ent in entities.items():
        current_ents[key] = ent.copy()

    for r in relations:
        # make sure all objects reference each other
        rel = Relation(r.r_type, r.from_text, r.to_text)
        e1 = current_ents.get(rel.from_text)
        e2 = current_ents.get(rel.to_text)

        rel.set_ents(e1, e2)
        e1.outgoing_relations.append(rel)
        e2.incoming_relations.append(rel)

        cur_relations.append(rel)

    #check those dependencies
    for d in dependencies:
        if not d.check_dependency(current_ents):
            return []

    n = Network(current_ents, cur_relations, dependencies)
    return [n]




class Uuid:
    def __init__(self):
        self.cntr = 0

    def __call__(self, *args, **kwargs):
        self.cntr += 1
        return str(self.cntr)

    def __str__(self):
        return str(self.cntr)
