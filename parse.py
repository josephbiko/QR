import yaml
from datatypes import *


def parse(name="input.yaml"):
    entities = {}
    relations = []
    dependencies = []
    with open(name, 'r') as stream:
        data = yaml.safe_load(stream)
    for key, obj in data.items():
        if obj["type"] == "entity":
            entities[key] = parse_ent(key, obj)
        elif obj['type'] == "relation":
            relations.append(parse_rel(obj))
        elif obj['type'] == "dependency":
            dependencies.append(parse_dependency(obj))
        else:
            raise Exception(f"undefined type {obj['type']}")

    for rel in relations:
        # make sure all objects reference each other
        e1 = entities.get(rel.from_text)
        e2 = entities.get(rel.to_text)

        rel.set_ents(e1, e2)
        e1.outgoing_relations.append(rel)
        e2.incoming_relations.append(rel)

    return Network(entities, relations,dependencies)


def parse_ent(name, ent):
    derivative = None
    magnitude = None

    magnitudes = []
    current_magnitude = None
    for mag in ent['magnitude']:
        s = State(s_type=mag['type'], value=mag['val'])
        magnitudes.append(s)
        if mag['val'] == ent['current_magnitude']:
            current_magnitude = s
    assert current_magnitude is not None, f"current magnitude{ent['current_magnitude']} not found"
    magnitude = Magnitude(states=magnitudes, current=current_magnitude)

    derivatives = []
    current_derivative = None
    for der in ent['derivative']:
        s = State(s_type=POINT, value=der)
        derivatives.append(s)
        if der == ent['current_derivative']:
            current_derivative = s
    assert current_derivative is not None, f"current derivative{ent['current_derivative']} not found"
    derivative = Derivative(states=derivatives, current=current_derivative)
    return Entity(name, magnitude, derivative, [], [])


def parse_rel(rel):
    return Relation(r_type=rel['relation'], from_text=rel['from'], to_text=rel['to'])


def parse_dependency(dep):
    return Dependency(from_e=dep['from'], to_e=dep['to'], from_attr=dep['from_attr'], to_attr=dep['to_attr'],
                      from_val=dep['from_val'], to_val=dep['to_val'], restriction=dep['restriction'])


print(parse("qr.yaml"))
