#!/usr/bin/env python3
"""
Aurora 24/7 Runner
-----------------
This script runs Aurora continuously in a 24/7 mode, automatically
switching between day and night phases based on the time.
"""

import os
import sys
import time
import logging
import subprocess
import datetime
from typing import Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("aurora_runner.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("agent_garden.aurora_runner")

def determine_phase() -> str:
    """Determine the current phase based on the time of day."""
    current_hour = datetime.datetime.now().hour
    
    # Day phase: 8 AM to 8 PM
    if 8 <= current_hour < 20:
        return "day"
    else:
        return "night"

def run_phase(phase: str) -> dict:
    """Run a single phase using the garden.py main function directly."""
    try:
        logger.info(f"Starting {phase} phase")
        start_time = time.time()
        
        # Import here to avoid circular imports
        from garden import main
        
        # Set up command line arguments for garden.py
        # Save original argv
        original_argv = sys.argv.copy()
        
        # Set new argv for garden.py
        sys.argv = ['garden.py', '--phase', phase]
        
        # Run the main function
        main()
        
        # Restore original argv
        sys.argv = original_argv
        
        duration = time.time() - start_time
        logger.info(f"{phase.capitalize()} phase completed in {duration:.2f} seconds")
        
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error in {phase} phase: {str(e)}", exc_info=True)
        return {"error": str(e)}

def run_continuously(check_interval_minutes: int = 15):
    """
    Run Aurora continuously, checking the current phase every interval.
    
    Args:
        check_interval_minutes: How often to check if the phase should change (in minutes)
    """
    logger.info(f"Starting Aurora in 24/7 mode (checking phase every {check_interval_minutes} minutes)")
    
    last_phase = None
    
    while True:
        current_phase = determine_phase()
        
        # Only run if the phase has changed or this is the first run
        if current_phase != last_phase:
            logger.info(f"Phase changed to: {current_phase}")
            run_phase(current_phase)
            last_phase = current_phase
        else:
            logger.info(f"Staying in {current_phase} phase")
        
        # Wait for the next check
        logger.info(f"Sleeping for {check_interval_minutes} minutes")
        time.sleep(check_interval_minutes * 60)

def main():
    """Main entry point for the Aurora runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Aurora in 24/7 mode")
    parser.add_argument("--interval", type=int, default=15, 
                        help="Interval in minutes to check for phase changes")
    parser.add_argument("--single-run", action="store_true", 
                        help="Run once and exit (for testing)")
    parser.add_argument("--force-phase", choices=["day", "night"], 
                        help="Force a specific phase (for testing)")
    args = parser.parse_args()
    
    if args.single_run:
        phase = args.force_phase or determine_phase()
        logger.info(f"Running single {phase} phase")
        run_phase(phase)
    else:
        run_continuously(args.interval)

if __name__ == "__main__":
    main()
