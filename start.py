import os
import subprocess



# pip install コマンドを実行
subprocess.check_call(['pip', 'install', '-U', 'g4f[all]'])

print("SERVERを起動します・・・")

# uvicornを起動
subprocess.check_call(['uvicorn', 'beta:app', '--reload', '--host', '0.0.0.0', '--port', '5000'])
