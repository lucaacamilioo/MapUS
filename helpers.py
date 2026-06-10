from cs50 import SQL
from heapq import heappush, heappop
import itertools
import math


# --- HELPER CLASS FOR GRAPH ---
class Graph:
    def __init__(self):
        self.adjacency_list = {}


class Vertex:
    def __init__(self):
        self.value = None


class Edge:
    def __init__(self):
        self.distance = None
        self.vertex = None

    # Print objects as readable string
    def __repr__(self):
        return f"(Target: {self.vertex}, Dist: {self.distance})"


def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate the distance between two coordinates"""
    R = 6371000 # Eart's radius (m)
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    # Calculate inside the square root
    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2.0) ** 2
    
    # Calculate the Haversine Formula
    distance = 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return distance


def build_graph():
    """Build the graph from the database"""
    graph = Graph()
    db = SQL("sqlite:///mapus.db")

    # Initialize all nodes as empty dicts
    nodes = db.execute("SELECT id FROM nodes")
    for node in nodes:
        graph.adjacency_list[node["id"]] = []

    # Populate the edges
    edges = db.execute(
        "SELECT node_a_id, node_b_id, weight FROM edges"
        )
    for edge in edges:
        a_id = edge["node_a_id"]
        b_id = edge["node_b_id"]
        weight = edge["weight"]

        # Safety check, prevent KeyErrors
        if a_id in graph.adjacency_list and b_id in graph.adjacency_list:

            # Edge from A to B
            a_to_b = Edge()
            a_to_b.distance = weight
            a_to_b.vertex = b_id
            graph.adjacency_list[a_id].append(a_to_b)

            # Edge from B to A
            b_to_a = Edge()
            b_to_a.distance = weight
            b_to_a.vertex = a_id
            graph.adjacency_list[b_id].append(b_to_a)

    return graph
    

def dijkstra(graph, start, end):
    """Find the shortest path from start node to end node"""
    
    previous = {key: None for key in graph.adjacency_list.keys()}
    distances = {key: float("inf") for key in graph.adjacency_list.keys()}
    distances[start] = 0
    
    # Priority queue stores tuples: (cumulative_distance, node_id)
    pq = []
    heappush(pq, (0, start))

    while pq:
        current_distance, current_node = heappop(pq)

        # Skip stale entries in the priority queue
        if current_distance > distances[current_node]:
            continue

        # Early exit if we reached the target
        if current_node == end:
            break

        # Iterate over the vertex's edges using your custom Edge object
        for edge_obj in graph.adjacency_list[current_node]:
            neighbor = edge_obj.vertex
            weight = edge_obj.distance
            
            new_distance = current_distance + weight
            
            if new_distance < distances[neighbor]:
                distances[neighbor] = new_distance
                previous[neighbor] = current_node
                heappush(pq, (new_distance, neighbor))
    
    # Path distance validation
    if distances[end] == float("inf"):
        return [], float("inf")

    # Path Reconstruction
    path = []
    current = end
    while current is not None:
        path.insert(0, current) 
        current = previous[current]

    return path, distances[end]
