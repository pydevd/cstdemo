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

storage_client = storage.Client()
gsr_client = speech.SpeechClient()


class IndexView(views.MethodView):

    @property
    def app(self):
        """
        :rtype: app.FlaskApp
        """
        return flask.current_app

    def get(self):
        return flask.render_template('index.html')

    def post(self):
        LOG.info("new request")
        context = {}

        try:
            with mixutil.log_time("file received from request"):
                audio = self._get_audio_file_from_request()

            with mixutil.log_time("file saved to local file system"):
                flac_file_path = self._save_as_flac_to_local_fs(audio)

            with mixutil.log_time("file uploaded to google storage"):
                uri = self._upload_to_gs(flac_file_path)

            with mixutil.log_time("file sent to recognition"):
                audio = types.RecognitionAudio(uri=uri)
                rc_config = types.RecognitionConfig(
                    encoding=enums.RecognitionConfig.AudioEncoding.FLAC,
                    sample_rate_hertz=16000,
                    language_code='en-US',
                    enable_automatic_punctuation=True)

                operation = gsr_client.long_running_recognize(rc_config, audio)
                self.app.operation = operation

        except exc.FileUploadError as e:
            LOG.error("file processing error %s", logutil.format_exception(e))
            context['error'] = e.msg
            return flask.render_template('index.html', **context)

        return flask.redirect('status')

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

    def _upload_to_gs(self, flac_file_path: pathlib.Path) -> str:
        """Uploads flac file to Google Storage. Returns gs uri"""
        gs_bucket = storage_client.get_bucket(config.GS_BUCKET)
        blob = gs_bucket.blob(flac_file_path.name)
        blob.upload_from_filename(flac_file_path.as_posix())
        return 'gs://{}/{}'.format(config.GS_BUCKET, blob.name)
