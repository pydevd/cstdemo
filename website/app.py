import flask
from flask import views


class IndexView(views.MethodView):

    def get(self):
        return flask.render_template('index.html')


def create_app() -> flask.Flask:
    app = flask.Flask(__name__)

    app.add_url_rule('/', view_func=IndexView.as_view('index'))

    return app


app = create_app()
