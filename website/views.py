import pathlib

import flask
from flask import views
from google.cloud import speech
from google.cloud import storage
from google.cloud.speech import enums
from google.cloud.speech import types
from werkzeug.datastructures import FileStorage

import config
import exc
import flac
from utils import logutil
from utils import mixutil

LOG = logutil.get_logger(__name__)

gsr_client = speech.SpeechClient()
storage_client = storage.Client()


class IndexView(views.MethodView):

    @property
    def app(self):
        """

        :return: app.FlaskApp
        """
        return flask.current_app

    def get(self):
        return flask.render_template('index.html')

    def post(self):
        context = {}

        try:

            audio = self._get_audio_file_from_request()
            flac_file_path = self._save_as_flac_to_local_fs(audio)

            # upload file to Google Storage
            gs_bucket = storage_client.get_bucket(config.GS_BUCKET)
            blob = gs_bucket.blob(flac_file_path.name)
            blob.upload_from_filename(flac_file_path.as_posix())
            # start

            uri = 'gs://{}/{}'.format(config.GS_BUCKET, blob.name)

            audio = types.RecognitionAudio(uri=uri)

            rc_config = types.RecognitionConfig(
                encoding=enums.RecognitionConfig.AudioEncoding.FLAC,
                sample_rate_hertz=16000,
                language_code='en-US')

            operation = gsr_client.long_running_recognize(rc_config, audio)

            with mixutil.log_time("response = operation.result(timeout=90)"):
                response = operation.result(timeout=90)

            data = []
            with mixutil.log_time("for res in response.results"):
                for res in response.results:
                    data.append(res.alternatives[0].transcript)

            context['transcription'] = ' '.join(data)

        except exc.FileUploadError as e:
            LOG.error("file processing error %s", logutil.format_exception(e))
            context['error'] = e.msg

        return flask.render_template('index.html', **context)

    def _save_as_flac_to_local_fs(self, audio: FileStorage) -> pathlib.Path:
        if audio.filename.endswith('.flac'):
            filename = mixutil.unique_filename('flac')
            flac_file_path = config.TMP_DIR / filename
            audio.save(flac_file_path.as_posix())
            return flac_file_path

        filename = mixutil.unique_filename('mp3')
        mp3_file_path = config.TMP_DIR / filename

        filename = filename.replace('.mp3', '.flac')
        flac_file_path = config.TMP_DIR / filename

        audio.save(mp3_file_path.as_posix())

        flac.convert(mp3_file_path, flac_file_path)

        return flac_file_path

    def _get_audio_file_from_request(self) -> FileStorage:
        if 'file' not in flask.request.files:
            raise exc.FileUploadError("no file uploaded")

        audio: FileStorage = flask.request.files['file']

        if audio.mimetype not in config.ALLOWED_MIMETYPES:
            msg = "invalid file type: only .mp3 or .flac allowed"
            raise exc.FileUploadError(msg)

        return audio
