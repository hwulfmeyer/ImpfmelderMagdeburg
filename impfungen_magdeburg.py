import requests
import json
from datetime import datetime, timezone, timedelta
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, CallbackContext
import pickle

TG_BOT_TOKEN = ''
ignoreFirstFreSlotRequest = False

def sendTGMsg(msg):
    #tg_bot = Bot(token=TG_BOT_TOKEN)
    #tg_bot.send_message(chat_id = "-1001363330234", text=msg)
    print("SEND TG MESSAGE")


terminedict = {}
website = 'https://impfzentrum.termin-direkt.de/rest-v2/api/'
detailsRequest = requests.get(website + "Calendars/WithDetails")
msg = ""
msg += "https://impfzentrum.termin-direkt.de"
postMsg = False
for calender in detailsRequest.json()['Data']:
    msg += "\n"
    msg += calender['Name']
    firstFreeSlotRequest = requests.get(website + 'Calendars/' + str(calender['Id']) + '/FirstFreeSlot')
    firstFreeSlotRequestJson = firstFreeSlotRequest.json()
    
    servicesNames = {}
    dictFreeTermineNow = {}
    dictTotalTermine = {}
    for services in requests.get(website + 'Calendars/' + str(calender['Id']) + '/Services/WithDetails').json()['Data']:
        servicesNames[services['Id']] = services['Name']

    if ignoreFirstFreSlotRequest or (firstFreeSlotRequestJson['Success'] and firstFreeSlotRequestJson['Error'] is None and firstFreeSlotRequestJson['Data'] is not None):
        startDate = datetime.utcnow().replace(tzinfo=timezone.utc)+timedelta(hours=1)
        endDate = startDate+timedelta(days=28)
        payload = {"StartDate":startDate,"EndDate":endDate}
        scheduleRequest = requests.get(website + str(calender['Id']) + '/Schedules', data=payload)
        scheduleRequestJson = scheduleRequest.json()
        for days in scheduleRequestJson['Data']['Schedules']:
            for termin in scheduleRequestJson['Data']['Schedules'][days]:
                terminDatetime = datetime.fromisoformat(termin['Start'].replace("Z", "+00:00"))
                if terminDatetime > startDate:
                    dictTotalTermine[termin['ServiceId']] = dictTotalTermine.setdefault(termin['ServiceId'], 0) + termin['ConcurrentNum']
                    dictFreeTermineNow[termin['ServiceId']] = dictFreeTermineNow.setdefault(termin['ServiceId'], 0) + termin['FreeSeatsCount']
    
    
    msg += "\n"
    freeTermineNow = 0
    for serviceId, termine in dictFreeTermineNow.items():
        freeTermineNow += termine
        terminedict[serviceId] = terminedict.setdefault(serviceId, 0) + termine

    if freeTermineNow > 0:
        msg += "        Freie Termine:  " + str(freeTermineNow)
        for serviceId, termine in dictFreeTermineNow.items():
            msg += "\n                "+ servicesNames[serviceId] + ":  " + str(termine)
    else:
        msg += "        KEINE freien Termine!"
    
    msg += "\n"


picklefile = "termine.pkl"
try:
    filereader = open(picklefile, 'rb')
    savedterminedict = pickle.load(filereader)
except:
    savedterminedict = {}

for serviceId, freeTermineNow in terminedict.items():
    freeTermineLast = savedterminedict.setdefault(serviceId, 0)
    if freeTermineLast != freeTermineNow:
        if abs(freeTermineNow-freeTermineLast) > 50 or (freeTermineLast==0 or freeTermineNow==0):
            postMsg = True

if postMsg:
    filewriter = open(picklefile, 'wb')
    pickle.dump(terminedict, filewriter)
    sendTGMsg(msg)

print(msg)



"""
calenderId = 1
website = "https://impfzentrum.termin-direkt.de/rest-v2/api/Calendars/"

website =  website + str(calenderId) + "/"

payload = {"calendarId":calenderId,"serviceId":1,"personCount":1,"startDate":"2021-02-28T23:00:00.000Z","endDate":"2021-04-30T23:59:59.999Z","pendingReservations":[]}
headers = {'content-type': 'application/json'}
r = requests.post(website + 'DaysWithFreeIntervals', data=json.dumps(payload), headers=headers)

print(r.json())

payload = {"calendarId":calenderId,"serviceId":1,"personCount":1,"startDate":"2021-04-30","endDate":"2021-04-30","pendingReservations":[]}
headers = {'content-type': 'application/json'}
r = requests.post(website + 'FreeIntervals', data=json.dumps(payload), headers=headers)

print(r.json())"""