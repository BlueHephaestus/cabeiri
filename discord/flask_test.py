from flask import Flask, redirect
from utils.loop_utils import persistent
import time
from timeout_decorator import timeout

DAY = 3600*24
REFRESH_RATE = 1*DAY
INVITE_LENGTH_DURATION = 7*DAY

@timeout(5)
def run_app():
    redirect_url = time.time()
    print(redirect_url)
    app = Flask(__name__)

    @app.route('/')
    def index():
        #redirect_url = "https://example.com"
        return redirect(redirect_url)

    app.run(debug=True)

while True:
    try:
        run_app()
    except:
        pass
