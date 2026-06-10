from flask import Flask, render_template, request, jsonify
from cs50 import SQL
from helpers import Graph, Vertex, Edge, calculate_distance, build_graph, dijkstra
from flask_httpauth import HTTPBasicAuth
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
import os
import math

# Define the absolute path to the directory containing app.py
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, '.env')) # Force to look in this directory

# Initialize app
app = Flask(__name__)

# Force SQLite to use the absolute path to your database
db_path = os.path.join(BASE_DIR, "mapus.db")
db = SQL("sqlite:///mapus.db")

# Verify for admin page
auth = HTTPBasicAuth()
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")

# Prevent from spamming
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)


# --- PUBLIC FACING UI ---
@app.route("/")
def public_map():
    return render_template("public.html")


# Routing API
@app.route("/api/route", methods=["POST"])
@limiter.limit("60 per minute")
def calculate_route():
    # Get data from frontend, then validate
    data = request.get_json()
    if not data or 'start_node' not in data or 'end_node' not in data:
        return jsonify({"error": "Missing routing parameters."}), 400
    
    # Validate start_id and end_id
    try:
        start_id = int(data.get('start_node'))
        end_id = int (data.get('end_node'))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid node identifiers. Must be integers."}), 400

    try:
        # 1. Run the mathematical routing
        graph = build_graph()
        path, distance = dijkstra(graph, start_id, end_id)

        if not path:
            return jsonify({"error": "No physical path exists between these nodes"}), 404

        # 2. Extract the physical coordinates for the frontend
        nodes = db.execute("SELECT id, lat, lng FROM nodes")
        node_dict = {n['id']: [n['lat'], n['lng']] for n in nodes}

        # 3. Map the path sequence of IDs to their actual [lat, lng] coordinates
        coordinates = [node_dict[node_id] for node_id in path]

        # 4. Calculate Walking time (1.4 m/s avg)
        total_seconds = round(distance / 1.4)
        walk_minutes = total_seconds // 60
        walk_seconds = total_seconds % 60

        # Format the string exactly how the frontend needs it
        if walk_minutes > 0:
            time_string = f"{walk_minutes} min {walk_seconds} sec"
        else:
            time_string = f"{walk_seconds} seconds"

        # 5. Return the formatted data
        return jsonify({
            "distance_meters": round(distance, 2),
            "coordinates": coordinates,
            "path_sequence": path,
            "time_string": time_string
        }), 200

    except Exception as e:
        return jsonify({"error": "An internal server errors occured."}), 500


# --- ADMIN'S DASHBOARD ---
@auth.verify_password
def verify_password(username, password):
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        return username
    return None


@app.route("/admin-dashboard")
@auth.login_required
def index():
    return render_template("admin.html")


# --- LOCATIONS API ---
@app.route("/api/locations", methods=["GET"])
def get_locations():
    try:
        # Fetch all locations sorted alphabetically for the dropdown menus
        locations = db.execute(
            "SELECT l.node_id, l.name, l.category, n.lat, n.lng " \
            "FROM locations as l " \
            "JOIN nodes as n ON l.node_id = n.id " \
            "ORDER BY l.name ASC"
        )
        return jsonify(locations), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# API Endpoint to load all existing nodes on page refresh
@app.route("/api/nodes", methods=["GET"])
@auth.login_required
def get_nodes():
    nodes = db.execute("SELECT id, lat, lng FROM nodes")
    return jsonify(nodes)


# API to load all existing edges
@app.route("/api/edges", methods=["GET"])
@auth.login_required
def get_edges():
    try:
        edges = db.execute("""
        SELECT 
            e.id, 
            e.weight,
            n1.lat AS a_lat, n1.lng AS a_lng,
            n2.lat AS b_lat, n2.lng AS b_lng
        FROM edges e
        JOIN nodes n1 ON e.node_a_id = n1.id
        JOIN nodes n2 ON e.node_b_id = n2.id
        """)
        return jsonify(edges)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# API Endpoint to store a single node clicked on the map
@app.route("/admin/add-node", methods=["POST"])
@auth.login_required
@limiter.limit("15 per minute")
def add_node():

    # Get data and validate
    data = request.get_json()
    if not data or 'lat' not in data or 'lng' not in data:
        return jsonify({"error": "Missing routing parameters."}), 400

    # Get latitude and longitude, and validate
    try:
        lat = float(data.get('lat'))
        lng = float(data.get('lng'))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid node identifiers. Must be floating point numbers."}), 400
    
    # Try to insert queries, return the auto incremented primary key ID
    try:
        node_id = db.execute("INSERT INTO nodes (lat, lng) VALUES (?, ?)", lat, lng)
        return jsonify({"message": "Node saved succesfully", 
                        "id": node_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

# API Endpoint to link two existing nodes with a calculated weight
@app.route("/admin/add-edge", methods=["POST"])
@auth.login_required
def add_edge():

    # Get data and validate
    data = request.get_json()
    if not data or 'node_a_id' not in data or 'node_b_id' not in data:
        return jsonify({"error": "Missing routing parameters."}), 400

    # Get a_id and b_id, and validate
    try:
        a_id = int(data.get('node_a_id'))
        b_id = int(data.get('node_b_id'))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid node identifiers. Must be integers."}), 400

    # Try insert the edge to database
    try:

        # Getting lat & lng for nodes a & b
        node_a = db.execute("SELECT lat, lng FROM nodes WHERE id = ?", a_id)
        node_b = db.execute("SELECT lat, lng FROM nodes WHERE id = ?", b_id)

        # Validate both nodes
        if not node_a or not node_b:
            return jsonify({"error": "One or both node IDs do not exist"}), 400
        
        # Calculate weight (m)
        weight = calculate_distance(
            node_a[0]['lat'], node_a[0]['lng'],
            node_b[0]['lat'], node_b[0]['lng']
        )

        # Store the linked nodes / edge into the databse
        db.execute(
            "INSERT INTO edges (node_a_id, node_b_id, weight) VALUES (?, ?, ?)", a_id, b_id, weight
            )
        
        return jsonify({
            "message": "Edge link saved",
            "weight": weight
            }), 201

    # If database failure to be loaded
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

# API Endpoint to safely delete a node and all its connected edges
@app.route("/admin/delete-node", methods=["DELETE"])
@auth.login_required
@limiter.limit("10 per minute")
def delete_node():

    # Get data and validate
    data = request.get_json()
    if not data or 'node_id' not in data:
        return jsonify({"error": "Missing routing parameters."}), 400

    # Get node_id and validate
    try:
        node_id = int(data.get('node_id'))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid node identifiers. Must be integers."}), 400

    try:
        # Delete the edge which connect to the deleted node
        db.execute("DELETE FROM edges WHERE node_a_id = ? OR node_b_id = ?", node_id, node_id)
        
        # Destroy the physical node
        db.execute("DELETE FROM nodes WHERE id = ?", node_id)
        
        return jsonify({"message": f"Node {node_id} and orphaned edges destroyed"}), 200

    # Database failure to delete
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=False)