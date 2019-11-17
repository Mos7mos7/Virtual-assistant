from __future__ import print_function
import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import time 
import playsound
import speech_recognition as sr
from gtts import gTTS   #there is another module that works well it's pyttsx3 but i'am kinda google fan
import pytz
import subprocess

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
months=["january","feburary","march","april","june","may","august","july","septemper","october","novemeber","december"]
days=["saturday","sunday","monday","tuesday","wednesday","thursday","friday"]
ext=["rd","th","st","nd"]
def speak(text):
    tts=gTTS(text=text,lang="en")
    tts.save("voice.mp3")
    playsound.playsound("voice.mp3")

def getaud():
    r=sr.Recognizer()
    with sr.Microphone() as source:
        audio=r.listen(source)
        words=""

        try :
            words=r.recognize_google(audio)
            print(words)
        except Exception as ex:
            print("exception is :"+str(ex))
        
    return words.lower()




def auth_google():
    """function used to authinticate yourself for API"""
    
    creds = None
   
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)
    return service



def get_events(day,service):
    date=datetime.datetime.combine(day,datetime.datetime.min.time())
    end_date=datetime.datetime.combine(day,datetime.datetime.max.time())
    utc=pytz.UTC
    date=date.astimezone(utc)
    end_date=end_date.astimezone(utc) #formatting into utc to pass it below


    events_result = service.events().list(calendarId='primary', timeMin=date.isoformat(),timeMax=end_date.isoformat(),
                                         singleEvents=True,
                                        orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        speak('No upcoming events found.')
    else:
        speak(f"you have {len(events)} events on this day. ")
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        print(start, event['summary'])
        start_time=str(start.split("T")[1].split("-")[0])
        if int(start_time.split(":")[0])<12:
            start_time=start_time+"Am"
        else:
            start_time=str(int(start_time.split(":")[0])-12) + start_time.split(":")[1]#adding minutes
            start_time=start_time+"Pm"
        speak(event["summary"]+ " at "+ start_time)

def get_date(text):
    text=text.lower()
    today=datetime.date.today()
    if text.count("today")>0:
        return today
    day=-1
    day_of_week=-1
    month=-1
    year=today.year #assuming that we are talking in same year
    
    for word in text.split():
        if word in months:
            month=months.index(word)+1
        elif word in days:
            day_of_week=days.index(word)
        elif word.isdigit():
            day=int(word)
        else:
            for ex in ext:
                found=word.find(ex)
                if found > 0:
                    try:
                        day=int(word[:found])
                    except Exception as ex:
                        pass
    if month < today.month and month!=-1:   #next year this month passed
        year+=1
    if day<today.day and day!=-1 and month==-1:     #next day in the month day passed
        month+=1
    if month==-1 and day ==-1 and day_of_week!=-1:
        current_day=today.weekday()
        dif = day_of_week-current_day

        if dif <0:
            dif+=7
            if text.count("next")>=1:
                dif+=7
        return today+datetime.timedelta(dif)
    if month==-1 or day==-1 :
        return None
        
    return datetime.date(month=month, day=day, year=year)

def note(text):
    date=datetime.datetime.now()
    file_name=str(date).replace(":","-")+ "-note.txt"
    with open(file_name,"w") as f :
        f.write(text)

    subprocess.Popen(["gedit",file_name]) #gedit is the texit editor for linux it may varies on your machine

serv= auth_google()
cal_str=["what do i have","do i have plans","am i busy"]

text=getaud()
for word in cal_str:
    if word in text.lower():
        date=get_date(text)
        if date:
            get_events(date,serv)
        else:
            speak("please try again")
note_str=["make a note","write this down","remember this "]
for wrd in note_str:
    if word in text:
        speak("what you want to write ")
        note_text=getaud()
        note(note_text)
        speak("made it successfully")
