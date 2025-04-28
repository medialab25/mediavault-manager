from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

class TaskConfig(BaseModel):
    """Configuration for a scheduled task"""
    task_id: str = Field(..., description="Unique identifier for the task")
    task_type: Literal["interval", "cron", "date"] = Field(..., description="Type of task trigger")
    
    # Interval specific
    hours: Optional[int] = Field(None, description="Hours for interval trigger")
    minutes: Optional[int] = Field(None, description="Minutes for interval trigger")
    
    # Cron specific
    cron_hour: Optional[str] = Field(None, description="Cron hour expression")
    cron_minute: Optional[str] = Field(None, description="Cron minute expression")
    
    # Date specific
    run_date: Optional[datetime] = Field(None, description="Specific date to run the task")
    
    # Task function name (must be registered in scheduler)
    function_name: str = Field(..., description="Name of the function to execute")
    
    # Additional arguments for the task
    args: Optional[list] = Field(default=[], description="Arguments to pass to the task function")
    kwargs: Optional[dict] = Field(default={}, description="Keyword arguments to pass to the task function") 