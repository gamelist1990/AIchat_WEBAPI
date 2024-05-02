import os
import subprocess
import venv
import platform

# 仮想環境の作成
venv_dir = "./venv"
if not os.path.exists(venv_dir):
    venv.create(venv_dir)

# 仮想環境のパスを取得
venv_path = ''
if platform.system() == 'Windows':
    venv_path = os.path.join(venv_dir, 'Scripts', 'activate.bat')
elif platform.system() == 'Linux':  # LumixはLinuxベースのOSと仮定
    venv_path = os.path.join(venv_dir, 'bin', 'activate')

print("SERVERの起動準備中・・・")

# 仮想環境をアクティベート
if platform.system() == 'Windows':
    subprocess.check_call([venv_path, '&'])
else:
    subprocess.check_call(["source", venv_path], shell=True)

subprocess.check_call(['pip', 'install', '-r', 'requirements.txt'])
print("G4Fのインストール")
subprocess.check_call(['pip', 'install', '-U', 'g4f[all]'])
command = ['pip', 'uninstall', 'undetected-chromedriver']
process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
output, error = process.communicate(input=b'Y\n')

print("Output:", output.decode())
print("Error:", error.decode())

print("SERVER起動完了")

# uvicornを起動
subprocess.check_call(['uvicorn', 'beta:app', '--reload', '--host', '0.0.0.0', '--port', '5000'])
print("serverを0.0.0.0:5000で起動しました")
