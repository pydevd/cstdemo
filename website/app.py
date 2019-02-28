import flask


def create_app() -> flask.Flask:
    app = flask.Flask(__name__)

    @app.route('/')
    def _index():
        return flask.render_template('base.html')

    return app


app = create_app()
