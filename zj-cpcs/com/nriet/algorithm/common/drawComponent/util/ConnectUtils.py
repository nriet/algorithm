import paramiko
import os
import logging

def sshclient_execmd(hostname, port, username, password, execmd):
    s = paramiko.SSHClient()
    s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    s.connect(hostname=hostname, port=port, username=username, password=password)
    stdin, stdout, stderr = s.exec_command(execmd)

    line = stdout.readlines()
    logging.info(stderr.read())
    s.close()
    return line

# 测试方法
# if '__main__' == __name__:
#     hostname = '10.20.67.172'
#     port = 22
#     username = 'your hostname'
#     password = 'your password'
#     execmd = 'cd /usr; ls'
#     line=sshclient_execmd(hostname,port,username,password, execmd)
#     logging.info(line)
