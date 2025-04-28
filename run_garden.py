#!/usr/bin/env python3
"""
Agent Garden Scheduler
----------------------
This script runs the Agent Garden pulse system on a schedule.
It can be used with cron or as a long-running process.
"""

import os
import time
import schedule
import argparse
import logging
from datetime import datetime
from garden import pulse, load_agent_config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("garden_scheduler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("agent_garden")

def run_pulse(phase=None):
    """Run a pulse cycle with logging."""
    try:
        logger.info(f"Starting pulse cycle{f' in {phase} phase' if phase else ''}")
        results = pulse(force_phase=phase)
        logger.info(f"Pulse cycle completed successfully: {results}")
        return results
    except Exception as e:
        logger.error(f"Error in pulse cycle: {str(e)}", exc_info=True)
        return {"error": str(e)}

def setup_schedule(config):
    """Set up the schedule based on configuration."""
    day_phase_hour = config.get("pulse_settings", {}).get("day_phase_start_hour", 8)
    night_phase_hour = config.get("pulse_settings", {}).get("night_phase_start_hour", 20)
    
    # Schedule day phase
    schedule.every().day.at(f"{day_phase_hour:02d}:00").do(run_pulse, phase="day")
    logger.info(f"Scheduled day phase for {day_phase_hour:02d}:00 daily")
    
    # Schedule night phase
    schedule.every().day.at(f"{night_phase_hour:02d}:00").do(run_pulse, phase="night")
    logger.info(f"Scheduled night phase for {night_phase_hour:02d}:00 daily")

def main():
    """Main entry point for the scheduler."""
    parser = argparse.ArgumentParser(description="Run the Agent Garden scheduler")
    parser.add_argument("--run-once", action="store_true", help="Run once and exit")
    parser.add_argument("--phase", choices=["day", "night"], help="Force a specific phase for run-once mode")
    args = parser.parse_args()
    
    # Load configuration
    try:
        config = load_agent_config()
    except Exception as e:
        logger.error(f"Failed to load configuration: {str(e)}")
        return
    
    if args.run_once:
        # Run once and exit
        run_pulse(phase=args.phase)
    else:
        # Set up schedule and run continuously
        setup_schedule(config)
        
        logger.info("Agent Garden scheduler started")
        logger.info("Press Ctrl+C to exit")
        
        try:
            # Run pending jobs immediately
            schedule.run_pending()
            
            # Keep running
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
        except Exception as e:
            logger.error(f"Scheduler error: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main()
