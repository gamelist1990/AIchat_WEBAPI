import os
import subprocess

#subprocess.check_call(['pip','install','-r','requirements.txt'])
#print("G4Fのインストール")
#subprocess.check_call(['pip','install','-U','g4f[all]'])
#command = ['pip', 'uninstall', 'undetected-chromedriver']
#process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#output, error = process.communicate(input=b'Y\n')

#subprocess.check_call(['pip','list'])
# uvicornを起動subprocess.check_call(['wget', 'https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb'])subprocess.check_call(['sudo', 'apt', 'install', './google-chrome-stable_current_amd64.deb'])

subprocess.check_call(['uvicorn', 'beta:app', '--reload', '--host', '0.0.0.0', '--port', '5000'])
