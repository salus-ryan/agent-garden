#!/usr/bin/env python3
"""
Agent Garden Cycle Runner
------------------------
This script runs multiple day/night cycles of the Agent Garden system.
"""

import os
import sys
import time
import argparse
import logging
import subprocess
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("cycle_runner.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("agent_garden.cycle_runner")

def run_cycle(cycle_number, phase=None):
    """Run a single cycle with the specified phase."""
    try:
        logger.info(f"Starting cycle {cycle_number}{f' in {phase} phase' if phase else ''}")
        start_time = time.time()
        
        # Build the command to run garden.py with the appropriate phase
        cmd = [sys.executable, 'garden.py']
        if phase:
            cmd.extend(['--phase', phase])
        
        # Run the command as a subprocess
        logger.info(f"Running command: {' '.join(cmd)}")
        process = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # Log the output
        if process.stdout:
            logger.info(f"Output:\n{process.stdout}")
        if process.stderr:
            logger.warning(f"Errors:\n{process.stderr}")
        
        duration = time.time() - start_time
        logger.info(f"Cycle {cycle_number} completed in {duration:.2f} seconds")
        
        return {"success": True, "stdout": process.stdout, "stderr": process.stderr}
    except subprocess.CalledProcessError as e:
        logger.error(f"Error in cycle {cycle_number}: {str(e)}\nOutput: {e.stdout}\nError: {e.stderr}")
        return {"error": str(e), "stdout": e.stdout, "stderr": e.stderr}
    except Exception as e:
        logger.error(f"Error in cycle {cycle_number}: {str(e)}", exc_info=True)
        return {"error": str(e)}

def run_multiple_cycles(num_cycles, delay_minutes=0):
    """Run multiple day/night cycles with a delay between them."""
    for i in range(num_cycles):
        cycle_number = i + 1
        
        # Run day phase
        logger.info(f"=== Cycle {cycle_number} Day Phase ===")
        day_results = run_cycle(cycle_number, phase="day")
        
        # Wait between phases if specified
        if delay_minutes > 0:
            logger.info(f"Waiting {delay_minutes} minutes before night phase...")
            time.sleep(delay_minutes * 60)
        
        # Run night phase
        logger.info(f"=== Cycle {cycle_number} Night Phase ===")
        night_results = run_cycle(cycle_number, phase="night")
        
        # Wait between cycles if specified
        if i < num_cycles - 1 and delay_minutes > 0:
            logger.info(f"Waiting {delay_minutes} minutes before next cycle...")
            time.sleep(delay_minutes * 60)
        
        logger.info(f"Completed full cycle {cycle_number}")

def main():
    """Main entry point for the cycle runner."""
    parser = argparse.ArgumentParser(description="Run multiple Agent Garden cycles")
    parser.add_argument("--cycles", type=int, default=3, help="Number of cycles to run")
    parser.add_argument("--delay", type=int, default=0, help="Delay between phases in minutes")
    args = parser.parse_args()
    
    logger.info(f"Starting Agent Garden Cycle Runner with {args.cycles} cycles")
    run_multiple_cycles(args.cycles, args.delay)
    logger.info("All cycles completed")

if __name__ == "__main__":
    main()
