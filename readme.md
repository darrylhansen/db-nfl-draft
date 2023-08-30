## Instructions for A

Walk through the below instructions to get this project working

## One-Time Commands
### You'll need to run these commands one time to setup the project, virtual environment and dependencies
pip install virtualenv

virtualenv venv

source venv/bin/activate

pip install openai

pip install python-dotenv

pip install pandas

## Running the script

python dbdraft.py

## Running the script in subsequent sessions
### After the initial install is done if you come back into WSL you'll just need to reactivate the venv and then run the script.

source venv/bin/activate

python dbdraft.py

### When done

deactivate