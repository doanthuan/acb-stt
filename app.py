# -*- coding: utf-8 -*-
# import os
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS, cross_origin
from werkzeug.utils import secure_filename

import requests
from datetime import datetime
import joblib
import os
import sys
from utils import *

#from models.train_sentiment.DataSource import normalize_text
# from correct_spell import get_best_sentence
#from models import predict_topic
#from google_trans import transcribe_file
#from test_stream import transcribe_streaming


# filename = "./models/sentiment_model.joblib"
# clf = joblib.load(filename)


app = Flask(__name__, template_folder='./templates')
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

@app.route('/')
def main():
    return render_template('index.html')

@cross_origin()
@app.route('/uploadfile',methods=['POST'])
def uploadFile():
    # try:
       
    # except:
    #     print("Unexpected error:", sys.exc_info()[0])
    #     output = ""

    filename = upload_file()

    #start a call
    call_id = start_call()

    #preprocess, split audio by sentences
    list_sentences = preprocess(filename)
    for left_sen, right_sen in list_sentences:
        process_audio_sentence(left_sen, 1, call_id)
        process_audio_sentence(right_sen, 2, call_id)
    
    #stop a call
    stop_call()

    return(jsonify(result="success"))

@cross_origin()
@app.route('/uploadrecord',methods=['POST'])
def uploadRecord():
    try:
        filename = upload_file()
        filename = preprocess(filename)
        output = speech_to_text(filename)

        channel = int(request.form.get('channel'))
        print("channel",channel)

        # send to websocket
        send_msg(output, channel)

        # save conversation
        f= open("conversation.txt" ,"a+", encoding="utf-8")
        f.write(output+'\n')
        f.close()

    except:
        print("Unexpected error:", sys.exc_info()[0])
        output = ""
    
    return(jsonify(result=output))


@app.route('/start-call',methods=['GET'])
def start_call_test():
    start_call()
    return "success"


@app.route('/stop-call',methods=['POST'])
def stop_call():
    # read file content

    # # save conversation
    # f= open("conversation.txt" ,"r", encoding="utf-8")
    # output = f.read()
    # f.close()

    # document = normalize_text(output)
    # sentiment = clf.predict_proba([document])

    # topic = predict_topic(output)
    # topic = topic[0].replace("__label__", "")

    # #return [output, str(sentiment[0][0]), topic]
    # print(str(sentiment[0][0])+","+topic)

    data = {
            "callId": 100,
            # "sentiment": str(sentiment[0][0]),
            # "topic": topic
            }
    r = requests.post(API_URL+'/stt-demo/stop-call', json=data)
    return ""


if __name__ == '__main__':
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(host='0.0.0.0', port=5001, ssl_context=('cert.pem', 'key.pem'))
    #app.run(host='0.0.0.0', port=5001)