from parse import parse
from graphviz import Graph, Digraph
from datatypes import Uuid

uuid = Uuid()


def produce_networks(name="input.yaml"):
    network_counter = 0
    network = parse(name)
    networks = [network]
    stack = [network]
    while len(stack) > 0:
        network = stack.pop()
        new_networks = network.generate_spinoffs()
        stack += new_networks
        networks += new_networks
    return networks


def produce_graph(networks):
    basegraph = Digraph(engine='dot')  # fdp or dot
    graphs = {}
    global uuid
    for n in networks:
        n.init_count()
        with basegraph.subgraph(name=f"cluster_{n.hash}") as g:
            graphs[n.hash] = g
            for ent in n.entities.values():
                render_entitity(ent, g)

            for r in n.relations:
                ruuid = uuid()
                g.node(ruuid, r.r_type)
                g.edge(r.from_ent.uuid, ruuid)
                g.edge(ruuid, r.to_ent.uuid)
            g.attr(label=f"S_{n.count}")

    for n in networks:
        for r in n.root_of.values():
            if basegraph.engine == "dot":
                basegraph.edge(f"S_{n.count}", f"S_{r.count}")
            else:
                basegraph.edge(f"cluster_{n.hash}", f"cluster_{r.hash}")

    basegraph.render(format="png")


def render_entitity(ent, graph):
    global uuid
    ent.uuid = uuid()
    e = graph.node(ent.uuid, label=ent.name)

    m = str(ent.magnitude.current)
    ent.magnitude.uuid = uuid()
    d = str(ent.derivative.current)
    ent.derivative.uuid = uuid()

    graph.node(ent.magnitude.uuid, label=f"magnitude\n{m}")
    graph.node(ent.derivative.uuid, label=f"derivative\n{d}")

    graph.edge(ent.magnitude.uuid, ent.uuid)
    graph.edge(ent.derivative.uuid, ent.uuid)
    return graph


networks = produce_networks("qr.yaml")
produce_graph(networks)
