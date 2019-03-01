import pathlib
import subprocess

import config
import exc
from utils import logutil

LOG = logutil.get_logger(__name__)


def convert(mp3_file_path: pathlib.Path, flac_file_path: pathlib.Path):
    """Converts .mp3 file to .flac file using `sox` command line utility"""

    cmd = [
        config.SOX_EXEC_PATH.as_posix(),
        mp3_file_path.as_posix(),
        '--channels=1',
        '--rate=16000',
        '--bits=16',
        flac_file_path.as_posix()
    ]

    kwargs = {
        'stdout': subprocess.PIPE,
        'stderr': subprocess.PIPE
    }
    try:
        process = subprocess.Popen(cmd, **kwargs)
        process.wait()
    except Exception as e:
        raise exc.FlacConversionError from e

    if process.returncode != 0:
        msg = "return_code={}".format(process.returncode)
        raise exc.FlacConversionError(msg)

    if not flac_file_path.exists():
        msg = "{} was not created".format(flac_file_path.as_posix())
        raise exc.FlacConversionError(msg)
