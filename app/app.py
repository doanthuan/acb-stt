from typing import Dict

import requests
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS, cross_origin

from .config import settings
from .exceptions import APIException
from .utils import (extract_identity_info, preprocess, process_audio_sentence,
                    start_call, stop_call, upload_file)

# from models.train_sentiment.DataSource import normalize_text
# from correct_spell import get_best_sentence
# from models import predict_topic
# from google_trans import transcribe_file
# from test_stream import transcribe_streaming


# filename = "./models/sentiment_model.joblib"
# clf = joblib.load(filename)

app = Flask(__name__, template_folder="./templates")
cors = CORS(app)
app.config["CORS_HEADERS"] = "Content-Type"


@app.errorhandler(APIException)
def handle_error(e):
    return jsonify(e.to_dict())


@app.route("/")
def main():
    return render_template("index.html")


@cross_origin()
@app.route("/uploadfile", methods=["POST"])
def uploadFile():
    try:

        filename = upload_file()

        # start a call
        call_id = start_call()
        if call_id is None:
            raise ValueError("call_id cannot be None")

        # preprocess, split audio by sentences
        list_sentences = preprocess(filename)
        customer_text_sum = ""
        for left_sen, right_sen in list_sentences:
            process_audio_sentence(left_sen, 1, call_id)
            customer_text_sum += "." + process_audio_sentence(
                right_sen, 2, call_id, customer_text_sum
            )
        stop_call(call_id, filename)

        return jsonify(result="success")
    except Exception as e:
        print("Unexpected error:", e)
        raise e


@app.route("/start-call", methods=["GET"])
def start_call_test():
    start_call()
    return "success"


@app.route("/identity", methods=["POST"])
def read_identity_info() -> Dict:
    text = request.form.get("text", "")
    if text == "":
        raise APIException("`text` field is required")
    return extract_identity_info(text)


if __name__ == "__main__":
    app.jinja_env.auto_reload = True
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    app.run(host="0.0.0.0", port=60002, ssl_context=("cert.pem", "key.pem"), debug=True)
    # app.run(debug = True)
    # app.run(host='0.0.0.0', port=5001)
