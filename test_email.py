import smtplib

fromaddr = "from@example.com"
toaddrs = "doanvuthuan@gmail.com"
username = "4bc17ab6ea039c"
password = "da8dbd36e8a26a"
smtp_server = 'smtp.mailtrap.io'

message = f"""\
Subject: Hi Mailtrap
To: {toaddrs}
From: {fromaddr}

This is a test e-mail message."""



with smtplib.SMTP(smtp_server, 2525) as server:
    server.login(username, password)
    server.sendmail(fromaddr, toaddrs, message)
    server.quit()

