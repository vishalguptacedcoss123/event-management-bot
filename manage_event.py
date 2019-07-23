import sys
import os
from flask import Flask
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from event_management import event_data


app = Flask(__name__)


try:
    x = event_data(app)
    x.routing()
except Exception as e:
    print(str(e))


if __name__ == "__main__":
    app.run(debug=True,port=5003)