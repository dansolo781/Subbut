"""
Scheduler — avvia la scansione ogni 30 minuti
"""
import logging
from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)

def start_scheduler(scraper):
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        scraper.run_all,
        trigger="interval",
        minutes=30,
        id="subbuteo_scan",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler avviato — scansione ogni 30 minuti")
    # Prima scansione immediata all'avvio
    try:
        scraper.run_all()
    except Exception as e:
        logger.error(f"Prima scansione fallita: {e}")
    return scheduler
