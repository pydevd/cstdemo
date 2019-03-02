import flask


class FlaskApp(flask.Flask):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.operation = None


def create_app() -> flask.Flask:
    app = FlaskApp(__name__)

    from views import IndexView
    from views import StatusView

    app.add_url_rule('/', view_func=IndexView.as_view('index'))
    app.add_url_rule('/status/', view_func=StatusView.as_view('status'))

    return app


app = create_app()
