import credentials, requests
from flask import Flask, request
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
    if message['text']:
        respond = generate_message(message['text'])
        request_body = {
                'recipient': {
                    'id': sender_id
                },
                'message': {"text":respond}
            }
        response = requests.post('https://graph.facebook.com/v5.0/me/messages?access_token='+credentials.FB_ACCESS_TOKEN,json=request_body).json()
        return response
    return 'ok'

def generate_message(text):
    respond = ""
    if text == "1":
        respond = "hello"
    else: respond = "knock knock"
    return respond
if __name__ == "__main__":
    app.run(threaded=True, port=5000)