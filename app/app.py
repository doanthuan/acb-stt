import logging
import logging.config
import os
from typing import Dict

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS, cross_origin

from .exceptions import APIException
from .utils import (extract_identity_info, preprocess, process_audio_sentence,
                    start_call, stop_call, upload_file)

app = Flask(__name__, template_folder="./templates")


@app.before_first_request
def setup_app():
    setup_logging()
    CORS(app)
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
        call_id = start_call()
        if call_id is None:
            raise ValueError("call_id cannot be None")

        app.logger.info('start processing uploaded file')
        # preprocess, split audio by sentences
        list_sentences = preprocess(filename)
        customer_text_sum = ""
        for left_sen, right_sen in list_sentences:
            process_audio_sentence(left_sen, 1, call_id)
            customer_text_sum += "." + process_audio_sentence(
                right_sen, 2, call_id, customer_text_sum
            )
        stop_call(call_id, filename)
        app.logger.info('processing uploaded file finished')

        return jsonify(result="success")
    except Exception as e:
        app.logger.error(f"Unexpected error: {e}")
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


def setup_logging():
    from .config import settings
    from .logger import get_logging_config

    log_dir = settings.LOG_DIR
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    logging.config.dictConfig(get_logging_config())


if __name__ == "__main__":
    app.jinja_env.auto_reload = True
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    app.run(host="0.0.0.0", port=60002, ssl_context=("cert.pem", "key.pem"), debug=True)
    # app.run(debug = True)
    # app.run(host='0.0.0.0', port=5001)
