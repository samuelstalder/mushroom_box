import logging
from flask import Flask, g
from flask_minify import minify
import api
import front

app = Flask(__name__)

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(name)s : %(message)s')

minify(app=app, html=True, js=True, cssless=True, static=True)

app.register_blueprint(front.frontend)
app.register_blueprint(api.blueprint, url_prefix="/api")


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


if __name__ == "__main__":
    app.run(debug=True)
