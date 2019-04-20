# How to start
Make sure you have pipenv installed

1. `git clone https://github.com/alexpulich/itmo-ontologies-project`
2. `pipenv install`
3. Set up environmental variables VK_LOGIN and VK_PASSWORD with your VK credentials.
4. Set up the FLASK_APP environmental variable: `export FLASK_APP=app.py`
5. (optional) If you want to turn debug mode on: `export FLASK_DEBUG=TRUE`
6. To run the server: `flask run`