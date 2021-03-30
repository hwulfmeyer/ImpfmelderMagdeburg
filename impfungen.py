import requests
import json
from datetime import datetime, timezone, timedelta
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, CallbackContext
import pickle

TG_BOT_TOKEN = ''

def sendTGMsg(msg):
    tg_bot = Bot(token=TG_BOT_TOKEN)
    tg_bot.send_message(chat_id = "-1001363330234", text=msg)
    print(msg)


website = 'https://impfzentrum.termin-direkt.de/rest-v2/api/'
detailsRequest = requests.get(website + "Calendars/WithDetails")
msg = ""
msg += "https://impfzentrum.termin-direkt.de"
postMsg = False
for calender in detailsRequest.json()['Data']:
    if calender['Id'] == 13:
        continue
    msg += "\n"
    msg += calender['Name']
    firstFreeSlotRequest = requests.get(website + 'Calendars/' + str(calender['Id']) + '/FirstFreeSlot')
    firstFreeSlotRequestJson = firstFreeSlotRequest.json()
    
    freeTermineNow = 0
    totalTermine = 0
    if firstFreeSlotRequestJson['Success'] and firstFreeSlotRequestJson['Error'] is None and firstFreeSlotRequestJson['Data'] is not None:
        startDate = datetime.utcnow().replace(tzinfo=timezone.utc)
        endDate = startDate+timedelta(days=28)
        payload = {"StartDate":startDate,"EndDate":endDate}
        scheduleRequest = requests.get(website + str(calender['Id']) + '/Schedules', data=payload)
        scheduleRequestJson = scheduleRequest.json()
        for days in scheduleRequestJson['Data']['Schedules']:
            for termin in scheduleRequestJson['Data']['Schedules'][days]:
                totalTermine += termin['ConcurrentNum']
                if termin['FreeSeatsCount'] != 0:
                    freeTermineNow += termin['FreeSeatsCount']
    msg += "\n"
    if freeTermineNow != 0:
        msg += "\tFreie Termine: " + str(freeTermineNow)
    else:
        msg += "\tKEINE freien Termine!"

    freeTermineLast = 0
    picklefile = "calender"+str(calender['Id']) + ".pickle"
    try:
        filereader = open(picklefile, 'rb')
        freeTermineLast = pickle.load(filereader)
    except:
        freeTermineLast = 0
    if freeTermineLast!=freeTermineNow:
        if abs(freeTermineNow-freeTermineLast) > totalTermine*0.2 or (freeTermineLast==0 or freeTermineNow==0):
            postMsg = True
            filewriter = open(picklefile, 'wb')
            pickle.dump(freeTermineNow, filewriter)

if postMsg:
    sendTGMsg(msg)


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