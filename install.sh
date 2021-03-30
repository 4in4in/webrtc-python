sudo apt-get update && sudo apt-get upgrade
sudo apt-get install python3-dev
sudo apt-get install python3-pip
sudo apt-get install python3-venv

python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
