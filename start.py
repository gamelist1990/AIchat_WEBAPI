import os
import subprocess

#subprocess.check_call(['pip','install','-r','requirements.txt'])
#print("G4Fのインストール")
#subprocess.check_call(['pip','install','-U','g4f[all]'])
command = ['pip', 'uninstall', 'undetected-chromedriver']
process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
output, error = process.communicate(input=b'Y\n')

#subprocess.check_call(['pip','list'])
# uvicornを起動
subprocess.check_call(['uvicorn', 'beta:app', '--reload', '--host', '0.0.0.0', '--port', '5000'])
