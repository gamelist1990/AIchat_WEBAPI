import os
import subprocess

# ディレクトリを変更
os.chdir('g4f')

# 依存関係をインストール
subprocess.run(['pip', 'install', '-r', 'requirements.txt'])

# スクリプトを実行
subprocess.run(['python', 'beta.py'])
