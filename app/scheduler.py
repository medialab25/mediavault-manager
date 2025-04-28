from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from datetime import datetime, timedelta
from typing import Dict, Callable, Any

# Create a scheduler instance
scheduler = BackgroundScheduler()

# Dictionary to store registered task functions
task_registry: Dict[str, Callable] = {}

def register_task(name: str, func: Callable) -> None:
    """Register a task function with the scheduler"""
    task_registry[name] = func

def get_task_function(name: str) -> Callable:
    """Get a registered task function by name"""
    if name not in task_registry:
        raise ValueError(f"Task function '{name}' not registered")
    return task_registry[name]

def start_scheduler():
    """Start the scheduler and add default jobs"""
    if not scheduler.running:
        scheduler.start()
        
        # Example: Add a job that runs every hour
        scheduler.add_job(
            hourly_task,
            trigger=IntervalTrigger(hours=1),
            id='hourly_task',
            replace_existing=True
        )
        
        # Example: Add a job that runs at specific times
        scheduler.add_job(
            daily_task,
            trigger=CronTrigger(hour=0, minute=0),  # Run at midnight
            id='daily_task',
            replace_existing=True
        )

def stop_scheduler():
    """Stop the scheduler"""
    if scheduler.running:
        scheduler.shutdown()

def add_task(task_config: dict) -> None:
    """Add a new task to the scheduler"""
    task_id = task_config["task_id"]
    task_type = task_config["task_type"]
    function_name = task_config["function_name"]
    
    # Get the task function
    task_func = get_task_function(function_name)
    
    # Create the appropriate trigger
    if task_type == "interval":
        trigger = IntervalTrigger(
            hours=task_config.get("hours", 0),
            minutes=task_config.get("minutes", 0)
        )
    elif task_type == "cron":
        trigger = CronTrigger(
            hour=task_config.get("cron_hour", "*"),
            minute=task_config.get("cron_minute", "*")
        )
    elif task_type == "date":
        trigger = DateTrigger(run_date=task_config["run_date"])
    else:
        raise ValueError(f"Invalid task type: {task_type}")
    
    # Add the job to the scheduler
    scheduler.add_job(
        task_func,
        trigger=trigger,
        id=task_id,
        args=task_config.get("args", []),
        kwargs=task_config.get("kwargs", {}),
        replace_existing=True
    )

def remove_task(task_id: str) -> None:
    """Remove a task from the scheduler"""
    scheduler.remove_job(task_id)

# Example task functions
def hourly_task():
    """Task that runs every hour"""
    print(f"Running hourly task at {datetime.now()}")

def daily_task():
    """Task that runs daily at midnight"""
    print(f"Running daily task at {datetime.now()}")

# Register example tasks
register_task("hourly_task", hourly_task)
register_task("daily_task", daily_task)

# You can add more task functions here 