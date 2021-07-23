import smtplib

fromaddr = "from@example.com"
toaddrs = "doanvuthuan@gmail.com"
username = "minhpth"
password = "123456"
smtp_server = '10.56.240.52'
port = 25

message = f"""\
Subject: Hi Mailtrap
To: {toaddrs}
From: {fromaddr}

This is a test e-mail message."""



with smtplib.SMTP(smtp_server, port) as server:
    #server.login(username, password)
    smtp.ehlo()
    ntlm_authenticate(server, username, password)
    server.sendmail(fromaddr, toaddrs, message)
    server.quit()


from HTTPNtlmAuthHandler import asbase64
import ntlm
from smtplib import SMTPException, SMTPAuthenticationError

from base64 import decodestring

def ntlm_authenticate(smtp, username, password):
    """Example:
    >>> import smtplib
    >>> smtp = smtplib.SMTP("my.smtp.server")
    >>> smtp.ehlo()
    >>> ntlm_authenticate(smtp, r"DOMAIN\username", "password")
    """
    code, response = smtp.docmd("AUTH", "NTLM " + asbase64(ntlm.create_NTLM_NEGOTIATE_MESSAGE(username)))
    if code != 334:
        raise SMTPException("Server did not respond as expected to NTLM negotiate message")
    challenge, flags = ntlm.parse_NTLM_CHALLENGE_MESSAGE(decodestring(response))
    user_parts = username.split("\\", 1)
    code, response = smtp.docmd("", asbase64(ntlm.create_NTLM_AUTHENTICATE_MESSAGE(challenge, user_parts[1], user_parts[0], password, flags)))
    if code != 235:
        raise SMTPAuthenticationError(code, response)