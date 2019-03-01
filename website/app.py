import flask

import multiprocessing

import worker


class FlaskApp(flask.Flask):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.worker = None
        self.worker_tasks = multiprocessing.Queue()

        self.worker = multiprocessing.Process(target=worker.Worker(),
                                              args=(self.worker_tasks,))

        self.worker.start()

    def __del__(self):
        self.worker.kill()


def create_app() -> flask.Flask:
    app = FlaskApp(__name__)

    from views import IndexView

    app.add_url_rule('/', view_func=IndexView.as_view('index'))

    return app


app = create_app()
