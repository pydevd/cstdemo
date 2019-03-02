import flask
from flask import views

from utils import logutil
from google.api_core.exceptions import GoogleAPICallError

LOG = logutil.get_logger(__name__)


class StatusView(views.MethodView):

    @property
    def app(self):
        """
        :rtype: app.FlaskApp
        """
        return flask.current_app

    def _get_operation_results(self) -> str:
        parts = []
        try:
            response = self.app.operation.result()

        except GoogleAPICallError as e:
            LOG.error("can't get results %s", logutil.format_exception(e))
            response = None
            parts = ['Google Speech-to-Text API did not recognized ',
                     'text from uploaded file.']

        if response:
            for result in response.results:
                parts.append(result.alternatives[0].transcript)

        return ''.join(parts)

    def _get_progress_percent(self) -> int:
        progress_percent = -1
        if self.app.operation:
            self.app.operation.done()
            progress_percent = self.app.operation.metadata.progress_percent

        return progress_percent

    def get(self):
        progress_percent = self._get_progress_percent()
        text = None

        if progress_percent == 100:
            text = self._get_operation_results()

        return flask.render_template('status.html', progress=progress_percent,
                                     text=text)

    def post(self):
        progress = self._get_progress_percent()
        return flask.jsonify({"progress": progress})
