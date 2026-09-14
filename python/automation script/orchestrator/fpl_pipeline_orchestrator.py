import warnings
warnings.filterwarnings('ignore')

import os
import sys
import subprocess
import pandas as pd
from datetime import datetime, timedelta
import time
import logging
import json

# Configure logging with detailed output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fpl_pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
SEASON = "2627"
BASE_PATH = r"C:\Users\JesseOnu\fpl sql rework"
FILES_TO_RUN_PATH = os.path.join(BASE_PATH, "files to runn")
FIXTURES_CSV = os.path.join(BASE_PATH, "fixtures", f"{SEASON}fixtures.csv")

# Script names
SCRIPTS = {
    "get_fixtures": "get_fixtues.py",
    "fantasy_gw_data": "fantasy_gw_data.py",
    "gameweek_pull": "gameweek_pull.py",
    "player_scores": "player_scores.py",
    "fpl_player_pull": "fpl_player_pull-.py",
    "gameweek_pull_daily": "gameweek_pull.py",
    "assigning_classes": "assigning_classes.py",
    "sql_upload": "sql_table_upload_script.py"
}


class ScriptRunner:
    """
    Manages script execution with detailed logging and input handling.
    
    This class exists to:
    1. Track each script's execution (start time, end time, duration)
    2. Handle both input() prompts and hanging scripts gracefully
    3. Log everything to a JSON file for debugging multi-monitor issues
    
    Why separate into a class:
    - Cleaner state management (track which script is running)
    - Easier to debug (all execution details in one place)
    - Reusable for both daily and gameday tasks
    """
    
    def __init__(self, scripts_directory):
        self.scripts_dir = scripts_directory
        self.execution_log = []
    
    def run_script(self, script_name, script_file, requires_input=False, 
                   input_text="\n", delay_after=0, timeout=600):
        """
        Execute a Python script with robust input/output handling.
        
        HOW STDIN WORKS (This is the key part):
        
        When you run a script normally, it looks like:
            $ python myscript.py
            Enter your choice: _   <- Script waits here with input()
        
        You type something and press Enter. Python reads it from stdin.
        
        When you run via subprocess with input="\n":
            subprocess.run([sys.executable, script_path], input="\n", ...)
            
        Python simulates you typing a newline to that script's stdin.
        The script's input() call receives that newline and continues.
        
        This works because:
        - It doesn't depend on window focus (subprocess has no UI window)
        - It doesn't depend on which monitor is active
        - It's synchronous (script either gets input or times out)
        
        WHY pyautogui FAILS on dual monitors:
        - pyautogui.press('return') sends the key to the OS
        - The OS sends it to whichever window has focus
        - On dual monitors, you might be looking at monitor 1 while the
          subprocess is conceptually on monitor 2
        - Result: Enter key goes to your browser/IDE, not the subprocess
        
        Args:
            script_name: Display name (for logging)
            script_file: Filename in scripts directory
            requires_input: Does this script call input()?
            input_text: What to send to stdin (default "\n" = press Enter)
            delay_after: Wait N seconds before returning (throttle API calls)
            timeout: Max seconds to wait (default 600 = 10 min)
        
        Returns:
            dict with keys: success (bool), duration (float), stderr (str)
        """
        script_path = os.path.join(self.scripts_dir, script_file)
        start_time = datetime.now()
        
        try:
            # VALIDATION: Check if file exists first
            if not os.path.exists(script_path):
                error_msg = f"Script not found: {script_path}"
                logger.error(error_msg)
                self._log_execution(script_name, start_time, False, error_msg)
                return {'success': False, 'duration': 0, 'stderr': error_msg}
            
            logger.info(f"[{script_name}] Starting execution")
            logger.info(f"[{script_name}] File: {script_path}")
            logger.info(f"[{script_name}] Requires input: {requires_input}")
            
            # RUN THE SUBPROCESS
            # Key parameters:
            # - input=... sends data to subprocess stdin (only if requires_input=True)
            # - capture_output=True gets stdout/stderr for logging
            # - text=True means output is a string, not bytes
            # - timeout=... prevents hanging forever
            # - cwd=... runs the script from its own directory (matters for relative paths)
            result = subprocess.run(
                [sys.executable, script_path],
                input=input_text if requires_input else None,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.scripts_dir
            )
            
            duration = (datetime.now() - start_time).total_seconds()
            
            # CHECK IF IT SUCCEEDED
            if result.returncode == 0:
                logger.info(f"[{script_name}] Completed successfully ({duration:.1f}s)")
                if result.stdout:
                    logger.debug(f"[{script_name}] Output:\n{result.stdout[:500]}")  # First 500 chars
                
                self._log_execution(script_name, start_time, True, "", result.stdout)
                
                # Wait before next script (throttle)
                if delay_after > 0:
                    logger.info(f"[{script_name}] Waiting {delay_after}s before next task...")
                    time.sleep(delay_after)
                
                return {'success': True, 'duration': duration, 'stderr': ''}
            else:
                # SCRIPT FAILED (non-zero return code)
                error_msg = f"Script failed with return code {result.returncode}"
                logger.error(f"[{script_name}] {error_msg}")
                logger.error(f"[{script_name}] stderr:\n{result.stderr}")
                
                self._log_execution(script_name, start_time, False, result.stderr, result.stdout)
                return {'success': False, 'duration': duration, 'stderr': result.stderr}
        
        except subprocess.TimeoutExpired:
            # SCRIPT HUNG (took longer than timeout)
            duration = (datetime.now() - start_time).total_seconds()
            error_msg = f"Script exceeded timeout ({timeout}s). Likely waiting for input that wasn't sent."
            logger.error(f"[{script_name}] {error_msg}")
            logger.error(f"[{script_name}] DEBUGGING INFO:")
            logger.error(f"[{script_name}]   - Is the script calling input() without requiring input flag?")
            logger.error(f"[{script_name}]   - Is there a network/API call that's hanging?")
            logger.error(f"[{script_name}]   - Check the script for blocking operations")
            
            self._log_execution(script_name, start_time, False, error_msg)
            return {'success': False, 'duration': duration, 'stderr': error_msg}
        
        except Exception as e:
            # UNEXPECTED ERROR
            duration = (datetime.now() - start_time).total_seconds()
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"[{script_name}] {error_msg}")
            
            self._log_execution(script_name, start_time, False, error_msg)
            return {'success': False, 'duration': duration, 'stderr': error_msg}
    
    def _log_execution(self, script_name, start_time, success, stderr="", stdout=""):
        """
        Log execution details to both console and JSON file.
        
        The JSON file helps debug because:
        1. You can see exact timing (when did each script run?)
        2. You can see duration (how long did it take?)
        3. You can see success/fail pattern (does it always fail at the same script?)
        4. Useful when you're away and just checking the logs later
        """
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        log_entry = {
            'script_name': script_name,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_seconds': round(duration, 2),
            'success': success,
            'stderr': stderr[:200] if stderr else "",  # First 200 chars of error
            'stdout_preview': stdout[:200] if stdout else ""  # First 200 chars of output
        }
        
        self.execution_log.append(log_entry)
    
    def save_execution_log(self, filename='fpl_pipeline_executions.json'):
        """
        Save all execution details to JSON for analysis.
        
        This is useful because:
        - You can load it in Python and analyze patterns
        - You can share it to debug with someone else
        - It's timestamped so you can find specific runs
        """
        try:
            with open(filename, 'w') as f:
                json.dump(self.execution_log, f, indent=2)
            logger.info(f"Execution log saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save execution log: {e}")


def load_fixtures():
    """Load fixtures CSV and return as DataFrame."""
    try:
        fixtures_df = pd.read_csv(FIXTURES_CSV)
        logger.info(f"Loaded {len(fixtures_df)} fixtures from {FIXTURES_CSV}")
        return fixtures_df
    except FileNotFoundError:
        logger.error(f"Fixtures file not found: {FIXTURES_CSV}")
        return pd.DataFrame()


def parse_fixture_datetime(row):
    """
    Parse fixture kickoff_time into datetime object.
    Handles ISO 8601 format: 2026-08-21T19:00:00Z (UTC)
    """
    try:
        kickoff_time = row.get('kickoff_time')
        
        if pd.isna(kickoff_time) or kickoff_time == '':
            return None
        
        # Parse ISO 8601 format, pandas auto-detects Z as UTC
        fixture_dt = pd.to_datetime(str(kickoff_time))
        
        # Convert from UTC to local time, remove tz info for comparison
        fixture_dt = fixture_dt.tz_convert(None).tz_localize(None)
        
        return fixture_dt
    except Exception as e:
        logger.warning(f"Could not parse fixture datetime: {e}")
        return None


def get_upcoming_fixtures(fixtures_df, days_ahead=7):
    """
    Get fixtures within the next N days.
    
    Returns list of dicts with fixture info and calculated run times.
    """
    upcoming = []
    now = datetime.now()
    
    for idx, row in fixtures_df.iterrows():
        fixture_dt = parse_fixture_datetime(row)
        
        if fixture_dt is None:
            continue
        
        time_until = fixture_dt - now
        
        # Only future fixtures within the next days_ahead
        if timedelta(0) < time_until < timedelta(days=days_ahead):
            kickoff_plus_180 = fixture_dt + timedelta(minutes=180)
            upcoming.append({
                'fixture_dt': fixture_dt,
                'kickoff_plus_180': kickoff_plus_180,
                'home': row.get('home') or row.get('Home'),
                'away': row.get('away') or row.get('Away'),
                'time_until_kickoff': time_until,
                'time_until_180': kickoff_plus_180 - now
            })
    
    return upcoming


def run_daily_tasks(runner, delay_between_scripts=30):
    """
    Run tasks that execute every day at midnight.
    
    These scripts:
    1. gameweek_pull: Fetch updated prices and ownership (requires Enter press)
    2. fpl_player_pull: Fetch player data
    3. get_fixtures: Fetch fixture schedule
    4. fantasy_gw_data: Process and transform data
    5. sql_upload: Push to database
    """
    logger.info("=" * 70)
    logger.info("RUNNING DAILY TASKS (Midnight)")
    logger.info("=" * 70)
    
    # Format: (display_name, filename, requires_input)
    # requires_input=True means the script calls input() and we'll send "\n"
    daily_scripts = [
        ("gameweek_pull", SCRIPTS["gameweek_pull_daily"], True),
        ("fpl_player_pull", SCRIPTS["fpl_player_pull"], False),
        ("get_fixtures", SCRIPTS["get_fixtures"], False),
        ("fantasy_gw_data", SCRIPTS["fantasy_gw_data"], False),
        ("player_scores", SCRIPTS["player_scores"], False),
        ("sql_upload", SCRIPTS["sql_upload"], False)
    ]
    
    failed_scripts = []
    
    for i, (script_name, script_file, requires_input) in enumerate(daily_scripts):
        # Determine if we should wait after this script
        is_last_script = (i == len(daily_scripts) - 1)
        
        result = runner.run_script(
            script_name=script_name,
            script_file=script_file,
            requires_input=requires_input,
            input_text="\n" if requires_input else "",
            delay_after=0 if is_last_script else delay_between_scripts
        )
        
        if not result['success']:
            failed_scripts.append(script_name)
    
    # Summary
    logger.info("=" * 70)
    if failed_scripts:
        logger.warning(f"Daily tasks completed with failures: {', '.join(failed_scripts)}")
        return False
    else:
        logger.info("All daily tasks completed successfully")
        return True


def run_gameday_tasks(runner, delay_between_scripts=30):
    """
    Run tasks during gameday (when matches are playing).
    
    These scripts run multiple times throughout the day to track live updates:
    1. get_fixtures: Check fixture status
    2. fantasy_gw_data: Process updated data
    3. gameweek_pull: Fetch live points and prices (requires Enter press)
    4. player_scores: Detailed player scoring
    5. sql_upload: Push to database
    """
    logger.info("=" * 70)
    logger.info("RUNNING GAMEDAY TASKS")
    logger.info("=" * 70)
    
    gameday_scripts = [
        ("get_fixtures", SCRIPTS["get_fixtures"], False),
        ("fantasy_gw_data", SCRIPTS["fantasy_gw_data"], False),
        ("gameweek_pull", SCRIPTS["gameweek_pull"], True),
        ("player_scores", SCRIPTS["player_scores"], False),
        ("sql_upload", SCRIPTS["sql_upload"], False),
        ("assigning_classes", SCRIPTS["assigning_classes"], False)
    ]
    
    failed_scripts = []
    
    for i, (script_name, script_file, requires_input) in enumerate(gameday_scripts):
        is_last_script = (i == len(gameday_scripts) - 1)
        
        result = runner.run_script(
            script_name=script_name,
            script_file=script_file,
            requires_input=requires_input,
            input_text="\n" if requires_input else "",
            delay_after=0 if is_last_script else delay_between_scripts
        )
        
        if not result['success']:
            failed_scripts.append(script_name)
    
    logger.info("=" * 70)
    if failed_scripts:
        logger.warning(f"Gameday tasks completed with failures: {', '.join(failed_scripts)}")
        return False
    else:
        logger.info("All gameday tasks completed successfully")
        return True


def schedule_gameday_run(fixture_dt):
    """
    Calculate when to run gameday tasks and sleep until that time.
    
    Waits 180 minutes after fixture kickoff (enough time for match to finish
    and results to sync across FPL servers).
    
    Args:
        fixture_dt: datetime of fixture kickoff
    
    Returns: True
    """
    kickoff_plus_180 = fixture_dt + timedelta(minutes=180)
    now = datetime.now()
    
    if now >= kickoff_plus_180:
        logger.info("Gameday window has passed, running tasks immediately")
        return True
    
    wait_seconds = (kickoff_plus_180 - now).total_seconds()
    wait_minutes = wait_seconds / 60
    
    logger.info(f"Next gameday run scheduled for: {kickoff_plus_180.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Sleeping for {wait_minutes:.1f} minutes...")
    
    time.sleep(wait_seconds)
    return True


def main():
    """
    Main orchestrator.
    
    FLOW:
    1. Initialize the runner (tracks execution)
    2. Load fixtures (tells us when games are)
    3. Run daily tasks (midnight: refresh all data)
    4. Get upcoming fixtures in next 7 days
    5. For each fixture:
       a. Sleep until 180 min after kickoff
       b. Run gameday tasks
    6. Save execution log (for debugging)
    """
    logger.info("=" * 70)
    logger.info("FPL PIPELINE ORCHESTRATOR STARTED")
    logger.info("=" * 70)
    logger.info(f"Season: {SEASON}")
    logger.info(f"Base path: {BASE_PATH}")
    logger.info(f"Scripts directory: {FILES_TO_RUN_PATH}")
    
    # Initialize runner
    runner = ScriptRunner(FILES_TO_RUN_PATH)
    
    # Load fixtures
    fixtures_df = load_fixtures()
    if fixtures_df.empty:
        logger.error("No fixtures loaded. Exiting.")
        return
    
    # Run initial daily tasks
    logger.info("")
    logger.info("PHASE 1: Running initial daily refresh")
    run_daily_tasks(runner)
    
    # Get upcoming fixtures
    logger.info("")
    logger.info("PHASE 2: Checking for upcoming fixtures")
    upcoming = get_upcoming_fixtures(fixtures_df, days_ahead=7)
    
    if upcoming:
        logger.info(f"Found {len(upcoming)} fixtures in next 7 days")
        
        # Sort by kick-off time (earliest first)
        upcoming_sorted = sorted(upcoming, key=lambda x: x['fixture_dt'])
        
        # Process each fixture
        for fixture_num, fixture in enumerate(upcoming_sorted, 1):
            logger.info("")
            logger.info(f"PHASE 3.{fixture_num}: Processing fixture {fixture_num} of {len(upcoming_sorted)}")
            logger.info(f"  Match: {fixture['home']} vs {fixture['away']}")
            logger.info(f"  Kickoff: {fixture['fixture_dt'].strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"  Gameday tasks scheduled for: {fixture['kickoff_plus_180'].strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Sleep until gameday time, then run tasks
            if schedule_gameday_run(fixture['fixture_dt']):
                run_gameday_tasks(runner)
                logger.info(f"  Completed gameday tasks for {fixture['home']} vs {fixture['away']}")
            
            logger.info("")
    else:
        logger.info("No upcoming fixtures in next 7 days")
    
    # Save execution log
    logger.info("")
    logger.info("PHASE 4: Saving execution log")
    runner.save_execution_log()
    
    logger.info("=" * 70)
    logger.info("FPL PIPELINE ORCHESTRATOR COMPLETED")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()