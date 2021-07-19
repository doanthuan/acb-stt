import logging
import logging.config
import os
import pathlib
from typing import Dict

import smtplib
from email.mime.text import MIMEText

from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_cors import CORS, cross_origin

from .call import start_call, stop_call
from .config import settings
from .exceptions import APIException
from .nlp import extract_identity_info
from .utils import do_stt_and_extract_info, preprocess, upload_file, load_sftp_files, get_sftp_file

app = Flask(__name__, template_folder="./templates")


@app.before_first_request
def setup_app():
    setup_logging()
    CORS(app)
    app.config["CORS_HEADERS"] = "Content-Type"
    app.logger.info("Sucessfully init app")


@app.errorhandler(APIException)
def handle_error(e):
    return jsonify(e.to_dict())


@app.route("/", methods=["GET"])
def main():
    ftp_files = load_sftp_files()
    return render_template("index.html", ftp_files=ftp_files)

@app.route("/send-email", methods=["POST"])
def send_email():
    status = ""
    try:
        data = request.get_json()
        if data is None:
            raise ValueError("Request params should be in JSON format")

        msg =  MIMEText(data["content"])
        msg["subject"] = data["subject"]
        msg["from"] = settings.SMTP_USER
        msg["to"] = data["to"]

        app.logger.info(f"Using following for send email: host={settings.SMTP_HOST} port={settings.SMTP_PORT}")
    
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            
            app.logger.info(f"Authenticate with mail server: user={settings.SMTP_USER}")
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_EMAIL, data["to"], msg.as_string())
            app.logger.info(f"Send email OK")
        status = "SUCCESS"
    except Exception as e:
        status = "ERROR"
        app.logger.error(f"Unexpected error occured: {e}")
        raise e
    finally:
        return jsonify({"status": status})


@app.route("/upload-ftp", methods=["POST"])
def upload_ftp():
    if request.method == 'POST':
        try:
            #get selected files
            #ftp_files = request.form.getlist('selected_files')

            filename = request.form.get("filename")

            #get sftp file to upload folder
            get_sftp_file(filename)

            #process a call
            process_a_call(filename)

            return jsonify(result="success")
        except Exception as e:
            app.logger.error(f"Unexpected error: {e}")
            raise e
    

def process_a_call(filename):
    try:
        call_id = start_call()
        if call_id is None:
            raise ValueError("call_id cannot be None")

        # preprocess, split audio by sentences
        # app.logger.info("start processing uploaded file")
        audio_segments, num_channels, audio_duration = preprocess(filename)

        criteria = {
            "detect_name": False,
            "detect_address": False,
            "detect_id": False,
            "detect_phone": False,
            # more fields
            "detect_card_no": False,
            "detect_acc_no": False,
        }

        if num_channels > 2:
            raise ValueError("Cannot handle audio which has number of channels >=2")

        # If customer leaves a voice message ==> recognize all
        is_voice_message = False
        if num_channels == 1:
            is_voice_message = True

        agent_text = {"names": "", "addresses": "", "id": "", "phone": "", "card_no": "", "acc_no": ""}
        customer_text = {"names": "", "addresses": "", "id": "", "phone": "", "card_no":"", "acc_no":""}
        for segment in audio_segments:
            if segment.channel == 1:
                agent_text, criteria = do_stt_and_extract_info(
                    call_id=call_id,
                    audio_segment=segment,
                    current_text=agent_text,
                    criteria=criteria,
                    is_voice_message=is_voice_message,
                )
            else:
                customer_text, criteria = do_stt_and_extract_info(
                    call_id=call_id,
                    audio_segment=segment,
                    current_text=customer_text,
                    criteria=criteria,
                    is_voice_message=is_voice_message,
                )
        stop_call(call_id, filename, audio_duration)

        return jsonify(result="success")
    except Exception as e:
        app.logger.error(f"Unexpected error: {e}")
        raise e

@cross_origin()
@app.route("/uploadfile", methods=["POST"])
def uploadFile():
    try:
        filename = upload_file()

        process_a_call(filename)

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


@app.route("/f/<path:path>", methods=["GET"])
def load_files(path):
    app.logger.info(f"Received streaming request for audio file: {path}")
    resource_path = os.path.join(settings.UPLOAD_DIR, path)
    if not os.path.exists(resource_path):
        raise APIException("resource not found", status_code=404)

    # return Response(stream(), mimetype="audio/x-wav")
    # app_dir = str(pathlib.Path(__file__).parent.resolve())
    # return send_from_directory(app_dir + "/../" + settings.UPLOAD_DIR, path)
    upload_dir = os.path.abspath(settings.UPLOAD_DIR)
    return send_from_directory(upload_dir, path)


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
