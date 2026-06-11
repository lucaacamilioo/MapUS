# MapUS
#### Video Demo: [https://youtu.be/KWc-SZ-gAXY] (https://youtu.be/KWc-SZ-gAXY)
#### Description: 
MapUS is a Flask-based campus navigation application built for Universitas Gadjah Mada (UGM). It uses a graph model and Dijkstra's algorithm to compute the shortest walking route between campus locations, then renders the result with Leaflet.js.

Then open the public interface at:

```
https://lucaacamilioo.pythonanywhere.com/
```

## Features

- Public map interface with search and fast access points
- Route calculation endpoint using campus graph data
- Walking distance and time estimates
- Admin dashboard for adding nodes and edges to the campus map
- SQLite database storage for nodes, edges, and location metadata
- HTTP Basic authentication for administration
- Rate limiting to prevent abuse

## Project Structure

- `app.py` - Flask application with public UI, route API, admin APIs, and authentication
- `helpers.py` - Graph, Dijkstra, distance calculation, and graph construction utilities
- `requirements.txt` - Python dependencies
- `templates/` - HTML templates for public and admin pages
- `static/` - CSS and JavaScript files for frontend behavior and styling
- `.env` - environment variables for admin credentials

## Requirements

- Python 3.8+
- Flask
- Flask-Session
- Flask-HTTPAuth
- Flask-Limiter
- python-dotenv
- cs50
- requests

## Setup

1. Create and activate a Python virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the App

Start the Flask application with:

```bash
python app.py
```

or

```bash
flask run
```

## Notes

- The admin interface requires HTTP Basic authentication using values from `.env`.
- Node and edge insertion is managed through the admin dashboard and saved in SQLite.
- The public route API returns route coordinates and walking time estimates for frontend mapping.

## License

This project was created as a final project for CS50. Feel free to adapt it for personal learning or campus navigation prototypes.
