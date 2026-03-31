"""
Subbuteo Watcher — Flask app principale
"""
from flask import Flask, render_template, jsonify
from scraper import SubbuteoScraper
from database import Database
from scheduler import start_scheduler
import threading

app = Flask(__name__)
db = Database()
scraper = SubbuteoScraper(db)

@app.route("/")
def index():
    listings = db.get_all_listings()
    stats = db.get_stats()
    return render_template("index.html", listings=listings, stats=stats)

@app.route("/api/listings")
def api_listings():
    listings = db.get_all_listings()
    return jsonify(listings)

@app.route("/api/stats")
def api_stats():
    return jsonify(db.get_stats())

@app.route("/api/scan")
def api_scan():
    """Avvia una scansione manuale"""
    thread = threading.Thread(target=scraper.run_all)
    thread.daemon = True
    thread.start()
    return jsonify({"status": "ok", "message": "Scansione avviata"})

if __name__ == "__main__":
    start_scheduler(scraper)
    app.run(debug=True, port=5000, use_reloader=False)
