import schedule
import time
import logging
from utils.data_collection import data_collector
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def collect_historical_data():
    """Initial historical data collection"""
    logger.info("Starting historical data initialization")
    try:
        # Initialize database first
        data_collector.init_database()
        
        # Collect one year of historical data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        data_collector.collect_and_store_data(start_date.date(), end_date.date())
        
        logger.info("Historical data initialization completed")
    except Exception as e:
        logger.error(f"Error in historical data initialization: {str(e)}")
        logger.debug("Stack trace:", exc_info=True)
        raise

def run_scheduler():
    """Run the scheduler"""
    try:
        # First run: collect historical data
        collect_historical_data()
        logger.info("Initial data collection completed")
        
        # Schedule daily updates
        schedule.every().day.at("00:00").do(
            lambda: data_collector.collect_and_store_data()
        )
        
        logger.info("Scheduler started. Will collect new data daily.")
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            
    except Exception as e:
        logger.error(f"Critical error in scheduler: {str(e)}")
        logger.debug("Stack trace:", exc_info=True)
        raise

if __name__ == "__main__":
    run_scheduler()
