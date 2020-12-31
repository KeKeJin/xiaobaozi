import credentials, requests
from flask import Flask, request
import csv
import os
import time
import atexit
from apscheduler.schedulers.background import BackgroundScheduler  # schedules the message
from bible import books_list, chapters_of_book
import shelve

app = Flask(__name__)
def sendBibleNotification():
    bibleReaderIDs, biblePassages = getBibleReadersInfo()
    for i in range(len(bibleReaderIDs)):
        request_body = {
                        'recipient': {
                            'id': bibleReaderIDs[i]
                        },
                        'message': {"text":"Remember to read {} Chapter !".format(biblePassages[i][0], biblePassages[i][1])}
                        }
        response = requests.post('https://graph.facebook.com/v5.0/me/messages?access_token='+credentials.FB_ACCESS_TOKEN,json=request_body).json()

def sendWaterDrinkingNotification():
    water_ids, cups_list = getWaterUsersInfo()
    for i in range(len(water_ids)):
        request_body = {
                        'recipient': {
                            'id': water_ids[i]
                        },
                        'message': {"text":"You have drank {} cups of water today! You need to drink {} more cups!".format(cups_list[i], 8-cups_list[i])}
                        }
        response = requests.post('https://graph.facebook.com/v5.0/me/messages?access_token='+credentials.FB_ACCESS_TOKEN,json=request_body).json()

cron = BackgroundScheduler(daemon = True)
cron.add_job(func = sendBibleNotification, trigger = "cron", day = *)
cron.add_job(func =  sendWaterDrinkingNotification, trigger = "cron", hour = */23)
cron.start()

@app.route("/", methods=['GET'])
def root():
    output = request.get_json()
    return 'ok'

# Adds support for GET requests to our webhook
@app.route('/webhook',methods=['GET'])
def webhook():
    verify_token = request.args.get("hub.verify_token")
    # Check if sent token is correct
    if verify_token == credentials.WEBHOOK_VERIFY_TOKEN:
        # Responds with the challenge token from the request
        return request.args.get("hub.challenge")
    return 'Unable to authorise.'

@app.route("/webhook", methods=['POST'])
def webhook_handler():
    data = request.get_json()
    message = data['entry'][0]['messaging'][0]['message']
    sender_id = data['entry'][0]['messaging'][0]['sender']['id']
    print(message)
    try:
        if message['attachments'][0]['type'] == 'image':
            # generate response
            current_water_level = waterPlusOne(sender_id)
            respond = "Good job!! This is the {}th cup of water you have drank today!!".format(current_water_level)
            request_body = {
                        'recipient': {
                            'id': sender_id
                        },
                        'message': {"text":respond}
                    }
            response = requests.post('https://graph.facebook.com/v5.0/me/messages?access_token='+credentials.FB_ACCESS_TOKEN,json=request_body).json()
            
            return response
    except:
        if message['text']:
            respond = generate_message(message['text'], sender_id)
            request_body = {
                    'recipient': {
                        'id': sender_id
                    },
                    'message': {"text":respond}
                }
            response = requests.post('https://graph.facebook.com/v5.0/me/messages?access_token='+credentials.FB_ACCESS_TOKEN,json=request_body).json()
            return response
    return 'ok'

""" generate responding message"""
def generate_message(text, sender_id):
    respond = ""
    if text == "m" or text == "M":
        respond = "1. Bible Reading Daily Reminder \n2. Track Water Consumption"
    elif text == "2":
        # read water consumption data from file 
        with shelve.open('water') as db:
            if db[sender_id]:
                respond = "You have drank {} cups of water today!".format(db[sender_id])
            else: respond = "You have not drank any water today! Drank more water!"
        
    elif text == "1":
        try:
            book, chapter = getBibleReader(sender_id)
            print(book,chapter)
            respond = "You are currently enrolled in Bible reading plan! You next chapter is {} Chapter {}.".format(book, chapter)
        except:
            respond = "You have not registered your bible reading plan. Type 'bible reading plan' + book + chapter to start!"

    elif text[:17] == "reset water level" or text[:17] == "Reset water level":
        reset_water_level = waterPlusOne(sender_id, text[18:])
        respond = "You have reset your water level to {} cups.".format(text[18:])
    elif text[:18] == "bible reading plan" or text[:18] == "Bible reading plan":
        request = text.split()
        print(request)
        try:
            book = request[3]
            chapter = request[4]
        except:
            return "Please ender the book and the chapter!"
        respond = registerUserToBibleReading(sender_id, book, int(chapter))
       
    elif text == "done reading" or text == "Done reading":
        updateBibleReadingPlan(sender_id)
        with shelve.open('bibleReading') as db:
            if sender_id in db:
                respond = "Nice job! I will remind you to read the next chapter tomorrow!"
            else:
                respond = "You have not registered your bible reading plan. Type 'bible reading plan' + book + chapter to start!"
    else: respond = "Huh?"
    return respond

""" log water comsuption record of the day"""
def waterPlusOne(user, reset = None):
    # check if it is a new day than last modified
    modification_date = time.localtime(os.path.getmtime('water.csv'))
    current_date = time.localtime()
    current_water_level = 0
    if modification_date.tm_year == current_date.tm_year and modification_date.tm_mon == current_date.tm_mon and modification_date.tm_mday == current_date.tm_mday:
    
        # read water consumption data from db
        with shelve.open('water') as db:
            if user in db:
                db[user] = db[user] + 1
                current_water_level = db[user]
            else:
                db[user] = 1
                current_water_level = db[user]
    # if it is a new day
    else:
        with shelve.open('water') as db:
            db[user] = 1
            current_water_level = 1
    if reset:
        with shelve.open('water') as db:
            db[user] = reset
            current_water_level = db[user]
    return current_water_level

"""get the list of the water drinking users from the db"""
def getWaterUsersInfo():
    with shelve.open("water") as db:
        user_list = list(db.keys())
        cups_list = list(db.values())
    return user_list, cups_list

"""get the list of bible reading users from the database"""
def getBibleReadersInfo():
    with shelve.open('bibleReading') as db:
        users_list = list(db.keys())
        chapters_list = list(db.values())
    return users_list, chapters_list

"""get the book the user is reading"""
def getBibleReader(sender_id):
    with shelve.open('bibleReading') as db:
        [book, chapter] = db[sender_id]
    return book, chapter

"""Register user to the bibleReading database"""
def registerUserToBibleReading(user_id, book, chapter):
    if book in books_list:
        if chapter <= chapters_of_book[book]:
            with shelve.open('bibleReading') as db:
                db[user_id] = [book, chapter]
            print("sucessfully register!")
            return "Welcome to Bible reading daily plan! \nI will remind you every 24 hours!\n Please remember to read {} Chapter {} today!".format(book, chapter)
        else:
            return "Please enter a valid chapter number"
    else:
        return "Please enter a valid book name. Example, Genesis, Mark,..."

"""after user has finished the reading plan of the day,
update the bible reading plan in the data base for next day's reading plan"""
def updateBibleReadingPlan(user_id):
    with shelve.open('bibleReading') as db:
        [book, chapter] = db[user_id]
        nextBook, nextChapter = getNextBookAndChapter(book, int(chapter))
        db[user_id] = [nextBook, nextChapter]
        print("bible reading plan updated")

"""a helper function for updateBileReadingPlan, to get the book
to read for the next day. If there are more chapters left in the book, 
the next book is the same book. If there is no more chapter left to read,
the next day's book is the next book in the bible. If there are no more
book in the bible, the next book is genesis"""
def getNextBookAndChapter(book, chapter):
    last_chapter = chapters_of_book[book]
    if last_chapter > chapter:
        nextbook = book
        nextChapter = chapter + 1
    else:
        if book == 'Revelation':
            nextbook = 'Genesis'
        else:
            nextbook = books_list[books_list.index(book)+1]
        nextChapter = 1
    return nextbook, nextChapter


atexit.register(lambda: cron.shutdown(wait=False))
if __name__ == "__main__":
    app.run(threaded=True, port=5000)