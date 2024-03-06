import os
import subprocess



# pip install コマンドを実行
#subprocess.check_call(['pip', 'install', '-U', 'g4f[all]'])
#subprocess.check_call(['pip', 'install', '--upgrade', 'pip'])

#subprocess.check_call(['pip', 'uninstall', 'undetected_chromedriver'])

#subprocess.check_call(['pip', 'uninstall', 'browser_cookie3'])

print("SERVERを起動します・・・")

subprocess.check_call(['pip','install','sydney-py'])

# uvicornを起動
subprocess.check_call(['uvicorn', 'beta:app', '--reload', '--host', '0.0.0.0', '--port', '5000'])
