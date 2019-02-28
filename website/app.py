import contextlib
import logging
import pathlib
import time

import flask
from flask import views
from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types

tmp_dir = pathlib.Path('/tmp')

ALLOWED_MIMETYPES = ('audio/mp3', 'audio/flac')

LOG_FORMAT = '{asctime} | {levelname:.1} | {name:^24} |  {message}'


def get_logger(name: str) -> logging.Logger:
    """Creates logger with given name"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    handler = logging.StreamHandler()
    formatter = logging.Formatter(LOG_FORMAT, logging.Formatter.default_time_format, style='{')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


def configure():
    """Configures global logging settings"""
    logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT,
                        style='{', datefmt=logging.Formatter.default_time_format)

    tweak()


def tweak():
    """Tweak default loggers here"""
    # logging.getLogger('urllib3.connectionpool').disabled = True


LOG = get_logger(__name__)


class PostMessage:
    """Helper class.

    Attributes:
        message: String to be included into logging message

    Instance of this class returned by context manager. Main purpose is to
    include to log information, that can be extracted in context manager code
    block during runtime. For example:

    with log_time('hitting database...') as pm:
      rows = db.select('SELECT...')
      pm.message = 'fetched {} rows'.format(len(rows))

    """

    def __init__(self):
        self.message = ''


@contextlib.contextmanager
def log_time(message: str = ''):
    """Measures execution time of context manager's code block and writes
    execution time in seconds to the log after passed message.

    Args:
        message: Message to be displayed after code block executed.
        level: Logging level threshold.

    Yields:
        Instance of PostMessage inner class for additional messaging.
    """
    start_time = time.monotonic()
    pm = PostMessage()
    try:
        yield pm
    finally:
        msg = ' '.join((message, pm.message)) if pm.message else message
        execution_time = time.monotonic() - start_time
        LOG.info('%s (%.6fs)', msg, execution_time)


gsr_client = speech.SpeechClient()


class IndexView(views.MethodView):

    def get(self):
        return flask.render_template('index.html')

    def post(self):
        context = {}
        if 'file' not in flask.request.files:
            context["transcription"] = "[ NO FILE SELECTED ]"
        else:
            audio = flask.request.files['file']
            if audio.mimetype not in ALLOWED_MIMETYPES:
                context["transcription"] = "[ INVALID FILE TYPE ]"

            if audio.filename.endswith('.mp3'):
                # TODO: convert to .flac
                pass
            else:
                content = audio.stream.read()

            audio = types.RecognitionAudio(content=content)
            config = types.RecognitionConfig(
                encoding=enums.RecognitionConfig.AudioEncoding.FLAC,
                sample_rate_hertz=16000,
                language_code='en-US')

            operation = gsr_client.long_running_recognize(config, audio)

            with log_time("response = operation.result(timeout=90)"):
                response = operation.result(timeout=90)

            data = []
            with log_time("for res in response.results"):
                for res in response.results:
                    data.append(res.alternatives[0].transcript)

            context['transcription'] = ' '.join(data)

        return flask.render_template('index.html', **context)


def create_app() -> flask.Flask:
    app = flask.Flask(__name__)

    app.add_url_rule('/', view_func=IndexView.as_view('index'))

    return app


app = create_app()
