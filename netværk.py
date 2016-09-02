

import os
import sys
import argparse
import friendlytoml as toml
import subprocess

START = "start"
END = "slut"

def load_spec(path):
    if not os.path.exists(path):
        print("No file found at '{}'".format(path))
        return {}
    else:
        return toml.load(path)

class Node:
    def __init__(self, name, nid, duration, next_nodes):
        self.name = name.replace("_", " ").capitalize()
        self.nid = nid
        self.duration = duration
        self.next_nodes = next_nodes
        
        # Added later
        self.prev_nodes = set()
        self.first_start = 0
        self.last_start = 0
        self.first_end = 0
        self.last_end = 0
        self.slack = 0
        self.gen = 1
    
    def forward_traverse_from(self, node):
        """Enters the given node from another, updating the path to this one"""
        self.prev_nodes.add(node.nid)
        self.first_start = max(self.first_start, node.first_end)
        self.first_end = self.first_start + self.duration
        self.gen = max(self.gen, node.gen + 1)
    
    def backward_traverse_from(self, node):
        self.last_end = min(self.last_end, node.last_start) if self.last_end else node.last_start
        self.last_start = self.last_end - self.duration
        self.slack = self.last_end - self.first_end
    
    def __repr__(self):
        return "[{:^12}][{:^12}][{:^12}]\n[{:^40}]\n[{:^12}][{:^12}][{:^12}]".format(
            self.first_start, self.duration, self.first_end,
            self.name,
            self.last_start, self.slack, self.last_end
        )
    
    def __str__(self):
        return repr(self)

def shownodes(nodes):
    for nid, node in nodes.items():
        print(node)
        print(42*"-")
        
def create_dot(nodes, critical, ignored, end):
    cset = set(critical)
    igs = set(ignored)
    template = "digraph\n{}\n"
    
    nodetemp = """{nid} [shape = none; margin = 0; label = <
    <TABLE CELLSPACING="0" CELLPADDING="5">
      <TR> <TD> {first_start} </TD> <TD> {duration} </TD> <TD> {first_end} </TD> </TR>
      <TR><TD COLSPAN="3">{name}</TD></TR>
      <TR><TD>{last_start}</TD> <TD>{slack}</TD> <TD>{last_end}</TD></TR>
    </TABLE>>]"""
    
    igtemp = """{} [shape = box; label = "{}"]"""
    
    def reltemps(node):
        temps = []
        for nid in node.next_nodes:
            val = "{} -> {}{}".format(node.nid, nid,
                " [penwidth = 3]" if (nid in cset and node.nid in cset) else "")
            temps.append(val)
        return temps
    
    nodelist = [  # default settings
        "rankdir = LR"
    ]
    
    for node in nodes.values():
        if node in ignored:
            val = igtemp.format(node.nid, node.name)
        else:
            attrs = {
                'nid': node.nid,
                'first_start': node.first_start,
                'duration': node.duration,
                'first_end': node.first_end,
                'name': node.name,
                'last_start': node.last_start,
                'slack': node.slack,
                'last_end': node.last_end,
            }
            val = nodetemp.format_map(attrs)
        nodelist.append(val)
        if node.next_nodes and node.nid != end:
            nodelist.extend(reltemps(node))
    
    return template.format("{" + ";\n    ".join(nodelist) + "}")
    

def model(specname, spec, start, end):
    nodes = {}
    for name, attrs in spec.items():
        nodes[attrs['id']] = Node(name, attrs['id'], attrs['tid'], attrs['næste'])
    
    #print("============= After load ================")
    #shownodes(nodes)
    
    active = {}
    
    # forward pass
    current = [start]
    c = nodes[start]
    c.first_start = 0
    c.first_end = c.first_start + c.duration
    visited = set()
    while current:
        cid = current.pop()
        cur = nodes[cid]
        if cid != end:
            for nid in cur.next_nodes:
                node = nodes[nid]
                node.forward_traverse_from(cur)
                current.append(nid)
        visited.add(cid)
        active[cid] = cur
    nodes = active #  update the active names
    
    #print("============== After forward 1 =============")
    #shownodes(nodes)
    
    #if len(visited) != len(nodes):
    #    raise Exception("Unvisited node in the network!")
    
    # backward pass
    # Prepare data
    c = nodes[end]
    c.last_end = c.first_end
    c.last_start = c.first_start
    
    current = [end]
    visited = set()
    while current:
        cid = current.pop()
        cur = nodes[cid]
        for nid in cur.prev_nodes:
            node = nodes[nid]
            node.backward_traverse_from(cur)
            current.append(nid)
        visited.add(cid)
    
    print("============== After backward 1 =============")
    shownodes(nodes)
    
    # critical pass
    critical = []
    def add_critical(node, clist):
        clist.append(node.nid)
        if node != nodes[end]:
            for nnid in node.next_nodes:
                nnode = nodes[nnid]
                if nnode.slack == 0:
                    add_critical(nnode, clist)
    add_critical(nodes[start], critical)
    print("================== Critical =================")
    print(" -> " + " -> ".join([str(c) for c in critical]))
    
    print("================== Dot =================")
    ignored = {nodes[start], nodes[end]}
    dot = create_dot(nodes, critical, ignored, end)
    #print(dot)
    fpath = specname.rsplit(".", 1)[0] + ".gv"
    with open(fpath, "w") as f:
        f.write(dot)
    
    TARGET = "png"
    cmd = ["dot", "-O"]
    if TARGET == "png":
        cmd += ["-Tpng", "-s=100"]
    else:
        cmd += ["Tsvg"]
    
    print("Creating graph...")
    subprocess.call(cmd + [fpath])
    

def main(args=sys.argv[1:]):
    """entry point"""
    desc = "Laver et netværksdiagram ud fra den givne specifikation"
    parser = argparse.ArgumentParser(description = desc)
    
    parser.add_argument("spec")
    parser.add_argument("start_id", type=int)
    parser.add_argument("end_id", type=int)
    
    parsed = parser.parse_args(args)
    
    # start
    specname = parsed.spec
    spec = load_spec(specname)
    if spec:
        model(specname, spec, parsed.start_id, parsed.end_id)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()