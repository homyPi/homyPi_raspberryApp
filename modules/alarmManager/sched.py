from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone
import pytz
class Sched:
      scheduler = BackgroundScheduler(timezone=timezone('Europe/Paris'))
      scheduler.start()
      
      

      
