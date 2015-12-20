import sys
sys.path.append( "../../python" )
import dateutil.parser
import datetime
from sched import Sched
from hommy_utils import *
import pytz
import logging

import os
path = os.path.dirname(os.path.realpath(__file__))

LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName) '
              '-35s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)
logging.basicConfig(filename='module.log',level=logging.INFO, format=LOG_FORMAT)

class Alarm:
      name = None;
      serverRequester = None
      rabbitConnectionPlayer = None
      timezone=pytz.timezone('Europe/Paris')
      alarms = []
      def __init__(self, _id, hours, minutes, enable, repeat):
          self._id = _id
          self.hours = hours
          self.minutes = minutes
          self.enable = enable
          self.repeat = repeat
          self.nbTry = 0;
          self.job = None
          self.schedule()
          
          
      
      def execute(self):
        if not Utils.has_internet():
             #player = Player()
             #player.play_local()
             print("no connection")
        else:
            print("start alarm")
            if Alarm.serverRequester is not None:
                resp = Alarm.serverRequester.get('api/modules/music/playlists/generate?generator=musicgraph&musicSource=spotify')
                LOGGER.info(str(resp))
                if "err" in resp or "error" in resp:
                  if self.nbTry < 5:
                    self.execute()
                  else:
                    LOGGER.error("unable to start the alarm")
                else:
                  playlist = [];
                  if "playlist" in resp:
                    for item in resp["playlist"]:
                      if "track" in item:
                        track = item["track"]
                        if track is not None and "name" in track and "uri" in track:
                          newItem = {"source": "spotify", "uri": track["uri"], "name": track["name"]}
                          if "query" in item and "tempo" in item["query"]:
                            newItem["tempo"] = item["query"]["tempo"];
                          if "similarTo" in item:
                            newItem["similarTo"] = item["similarTo"]
                          LOGGER.info("track = " + str(newItem))
                          playlist.append(newItem)
                        else:
                          LOGGER.info(str(track))
                        print("===========")
                    print("finnaly, got " + str(len(playlist)) + "  songs");
                    Alarm.rabbitConnectionPlayer.emit('playListSet', {"trackset": playlist, "autoPlay": True})
                    
                    history = {
                      "execution_date": str(datetime.datetime.now()),
                      "executed_songs": playlist
                    }
                    print("set history");
                    resp = Alarm.serverRequester.post('api/modules/alarms/' + self._id + '/history', {"history": history});
                    LOGGER.info(str(resp))
                    if self.repeat is False:
                      resp = Alarm.serverRequester.put('api/modules/alarms/' + self._id, {"enable": False});
                      print(str(resp))
                      LOGGER.info(str(resp))

                  else:
                    LOGGER.error(resp)
                #if not self.repeat:
                #    self.enable = False
                #    Alarm.serverRequester.emit('alarm:update', {"alarm": {"_id": self._id, "update": {"enable": False}}})
             
          
          
      def schedule(self):
          if self.job is not None:
             self.job.remove()
          if self.enable is True:
             now = datetime.datetime.now()
             tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
             if (now.hour >= self.hours) and (now.minute >= self.minutes):
                self.time = tomorrow.replace(hour=self.hours, minute=self.minutes, second=0)
             else:
                self.time = now.replace(hour=self.hours, minute=self.minutes, second=0)
             self.job = Sched.scheduler.add_job(self.execute, 'date', next_run_time = self.time)
      @staticmethod
      def remove(alarm, notify=True):
            LOGGER.info("Removing alarm " + str(alarm._id));
            if alarm is not None:
              if alarm.job is not None:
                  alarm.job.remove()
              Alarm.alarms.remove(alarm)
              Alarm.notifySuccess("Alarm removed");
      @staticmethod
      def removeByData(data):
          alarmId = data['alarm']['_id'];
          alarm = None
          for a in Alarm.alarms:
              if alarmId == a._id:
                 alarm = a
          if alarm != None:
            Alarm.alarms.remove(alarm)
          else:
            Alarm.notifyError("unknown alarm");

      @staticmethod
      def setAlarmsFromJSON(items):
        error = False
        for data in items:
          if Alarm.addAlarmsFromJSON(data, False) is None:
            error = True
        if error:
          Alarm.notifyError("Unable to set alarms");
        else:
          Alarm.notifySuccess(str(len(items)) + " alarms added");
          
      @staticmethod
      def addAlarmsFromJSON(data, notify=True):
        if "hours" not in data or "minutes" not in data or "_id" not in data:
          if notify:
            Alarm.notifyError("invalid alarm");
          return None;
        hours = data['hours']
        minutes = data['minutes']
        LOGGER.info("new alarm at " + str(hours) + ":" + str(minutes))
        existingAlarm = Alarm.getByDate(hours, minutes)
        if existingAlarm is not None:
          if notify:
            Alarm.notifySuccess("Alarm at " + str(hours) + ":" + str(minutes) + " already exists")
          return existingAlarm;
        else:
          alarm = Alarm(data['_id'], hours, minutes, data['enable'], data['repeat'])
          Alarm.alarms.append(alarm)
          if notify:
            Alarm.notifySuccess("Alarm added at " + str(hours) + ":" + str(minutes) + "")
          return alarm;

      @staticmethod
      def updateAlarmFromJSON(alarm, notify=True):
        if "_id" not in data:
          if notify:
            Alarm.notifyError("invalid alarm's data");
          return None;
        existing = Alarm.getById(alarm["_id"])
        if existing is None:
          Alarm.notifyError("unknown alarm")
          return None;
        else:
          if existing.job is not None:
            existing.job.remove()
            existing.job=None
          if "hours" in data:
            existing.hours = data["hours"]
          if "minutes" in data:
            existing.minutes = data["minutes"]
          if "enable" in data:
            existing.enable = data["enable"]
          if "repeat" in data:
            existing.repeat = data["repeat"]
          existing.schedule();
          Alarm.notifySuccess("Alarm updated")

      @staticmethod
      def getById(id):
        a = None
        for alarm in Alarm.alarms:
          if alarm._id == id:
            a = alarm
            break;
        return a;
        
      @staticmethod
      def getByDate(hours, minutes):
          e = None
          for alarm in Alarm.alarms:
              if alarm.hours == hours and alarm.minutes == minutes:
                 e = alarm
                 break
          return e

      @staticmethod
      def notifySuccess(message):
        LOGGER.info(message);
        os.system("mplayer " + path + "/confirm.wav")
      @staticmethod
      def notifyError(message):
        LOGGER.error(message);
                 
               
              
      
          
