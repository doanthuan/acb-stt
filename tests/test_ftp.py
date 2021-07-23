from paramiko import file
import pysftp, paramiko
import sys

# path = './requirements.txt'
# localpath = "requirements.txt"

host = "206.189.32.123"                    #hard-coded
password = "dongkisot"                #hard-coded
username = "thuan"                #hard-coded
ftp_dir = "/home/thuan/stt"
local_dir = "upload"


# cnopts = pysftp.CnOpts()
# cnopts.hostkeys = None 
# with pysftp.Connection(host, username=username, password=password, cnopts=cnopts) as sftp:
#     sftp.get('out.txt')         # get a remote file


ssh = paramiko.SSHClient()
# automatically add keys without requiring human intervention
ssh.set_missing_host_key_policy( paramiko.AutoAddPolicy() )

ssh.connect(host, username=username, password=password)

ftp = ssh.open_sftp()
for filename in ftp.listdir(ftp_dir):
    if filename.endswith((".mp3")):
        #print(filename)
        ftp.get(f"{ftp_dir}/{filename}", f"{local_dir}/{filename}")
    