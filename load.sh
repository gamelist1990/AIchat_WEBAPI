pip install -r requirements.txt

pip install -U g4f[all]

echo y | pip uninstall undetected-chromedriver

uvicorn beta:app --reload --host 0.0.0.0 --port 5000
