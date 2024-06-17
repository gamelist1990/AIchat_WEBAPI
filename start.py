import subprocess
import sys

# コマンドをリスト形式で指定
cmd = ['uvicorn', 'beta:app', '--reload', '--host', '0.0.0.0', '--port', '5000']

# console.logをクリア
with open('console.log', 'w') as f:
    pass

# subprocessを開始し、標準出力と標準エラー出力を取得
process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

# subprocessの出力をconsole.logとターミナルに表示
with open('console.log', 'a') as f:
    for line in iter(process.stdout.readline, b''):
        line = line.decode('utf-8').rstrip()
        print(line)
        sys.stdout.write(line + '\n')
        sys.stdout.flush()
        f.write(line + '\n')
        f.flush() 

# subprocessが終了するまで待機
process.communicate()
