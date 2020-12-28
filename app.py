import credentials, requests
from flask import Flask, request
import csv
import os
import time
app = Flask(__name__)

@app.route("/", methods=['GET'])
def root():
    output = request.get_json()
    print(output)
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

    try:
        if message['attachments']:
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
    if text == "m":
        respond = "1. Track Packages \n2. Track Water Consumption"
    elif text == "2":
        # read water consumption data from file 
        water_consumption_dic = readWaterData()
        if water_consumption_dic[sender_id]:
            respond = "You have drank {} cups of water today!".format(water_consumption_dic[sender_id])
        else: respond = "You have not drank any water today! Drank more water!"
    elif text == "1":
        respond = "Package tracking is not avaliable"
    elif text[:17] == "reset water level":
        reset_water_level = waterPlusOne(sender_id, text[18:])
        respond = "You have reset your water level to {} cups.".format(text[18:])
    else: respond = "Huh?"
    return respond

def readWaterData():
    with open('water.csv') as f:
        water_consumption_dic = dict(filter(None,csv.reader(f)))
    return water_consumption_dic

""" log water comsuption record of the day"""
def waterPlusOne(user, reset = None):
    # check if it is a new day than last modified
    modification_date = time.localtime(os.path.getmtime('water.csv'))
    current_date = time.localtime()
    if modification_date.tm_year == current_date.tm_year and modification_date.tm_mon == current_date.tm_mon and modification_date.tm_mday == current_date.tm_mday:
    
        # read water consumption data from file 
        water_consumption_dic = readWaterData()

        if user in water_consumption_dic:
            water_consumption_dic[user] = str(int(water_consumption_dic[user]) + 1)
        else:
            water_consumption_dic[user] = "1"
    # if it is a new day
    else:
        water_consumption_dic = {}
        water_consumption_dic[user] = "1"

    if reset:
        water_consumption_dic[user] = reset
    with open('water.csv','w') as writeFile:
        writer = csv.writer(writeFile)
        for key, value in water_consumption_dic.items():
            writer.writerow([key, value])
    return water_consumption_dic[user]

if __name__ == "__main__":
    app.run(threaded=True, port=5000)