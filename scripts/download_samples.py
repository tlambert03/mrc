import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from dropbox import Dropbox

TEST_DATA = str(Path(__file__).parent.parent / "tests" / "data")
REMOTE_SAMPLES = "/dv_samples/"
TOKEN = os.getenv("DROPBOX_TOKEN")
assert TOKEN, "must set DROPBOX_TOKEN to download files"


def fetch(dbx: Dropbox, remote_path: str, local_dest: str):
    try:
        dbx.files_download_to_file(
            Path(local_dest) / Path(remote_path).name, remote_path
        )
        print(f"success: {remote_path}")
    except Exception as e:
        print(f"ERROR: {remote_path} ({e})")


def download_folder(dbx: Dropbox, remote_folder: str, local_dest: str):
    files = [
        (dbx, x.path_display, local_dest)
        for x in dbx.files_list_folder(remote_folder).entries
        if x.is_downloadable
    ]
    if not files:
        return
    Path(local_dest).mkdir(exist_ok=True)
    with ThreadPoolExecutor() as exc:
        print(f"downloading {remote_folder} ...")
        list(exc.map(lambda _: fetch(*_), files))


def main(dest: str = TEST_DATA):
    with Dropbox(TOKEN) as dbx:
        # Check that the access token is valid
        try:
            dbx.users_get_current_account()
        except Exception:
            sys.exit("ERROR: Invalid access token")
        download_folder(dbx, REMOTE_SAMPLES, dest)


if __name__ == "__main__":
    dest = sys.argv[sys.argv.index("--dest") + 1] if "--dest" in sys.argv else TEST_DATA
    main(dest=dest)
