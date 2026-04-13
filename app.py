import os
import threading
import logging
from flask import Flask, render_template, jsonify
from database import Database
from scraper import SubbuteoScraper
from scheduler import start_scheduler

logging.basicConfig(level=logging.INFO)

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
    return jsonify(db.get_all_listings())

@app.route("/api/stats")
def api_stats():
    return jsonify(db.get_stats())

@app.route("/api/scan")
def api_scan():
    thread = threading.Thread(target=scraper.run_all)
    thread.daemon = True
    thread.start()
    return jsonify({"status": "ok", "message": "Scansione avviata"})

if __name__ == "__main__":
    start_scheduler(scraper)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
