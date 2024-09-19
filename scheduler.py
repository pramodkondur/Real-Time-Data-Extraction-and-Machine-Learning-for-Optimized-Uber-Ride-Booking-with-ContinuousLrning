import schedule
import time
from mlflowtry import mlflow_run
from datetime import datetime, timedelta

def sleep_until(target_time):
    """Calculate the time difference between now and the target time, then sleep for that duration."""
    now = datetime.now()
    target_datetime = datetime.combine(now.date(), target_time)

    # If the target time has already passed today, schedule it for the next day
    if now > target_datetime:
        target_datetime += timedelta(days=1)

    time_to_sleep = (target_datetime - now).total_seconds()
    print(f"Sleeping for {time_to_sleep // 3600:.0f} hours and {(time_to_sleep % 3600) // 60:.0f} minutes.")
    time.sleep(time_to_sleep)


# Set the target time to 9:00 AM
target_time = datetime.strptime("09:00", "%H:%M").time()

# Run the MLFlow job at 9:00 AM every day
while True:
    sleep_until(target_time)
    mlflow_run()
