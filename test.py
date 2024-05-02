import os
import subprocess




print("SERVERの起動準備中・・・")

subprocess.check_call(['pip','install','-r','requirements.txt'])
#print("G4Fのインストール")
subprocess.check_call(['pip','install','-U','g4f[all]'])
#command = ['pip', 'uninstall', 'undetected-chromedriver']
#process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#output, error = process.communicate(input=b'Y\n')

#print("Output:", output.decode())
#print("Error:", error.decode())

print("依存関係のインストール完了")
subprocess.check_call(['pip','list'])
