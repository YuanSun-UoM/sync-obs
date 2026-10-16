#!/usr/bin/python3

import os
from argparse import ArgumentParser
from time import time, sleep
from zipfile import ZipFile, ZIP_DEFLATED
from datetime import date, datetime
from json import load as json_load
from dataclasses import dataclass
from shutil import disk_usage
from glob import glob
import subprocess
import tempfile
import shutil

ARCHIVE_MAX_FILL_FRACTION_MIN = 0.1
ARCHIVE_MAX_FILL_FRACTION_MAX = 0.98


@dataclass
class Config:
    source: str
    destination: str
    _archive_dir: str
    delete_empty_dirs: bool
    archive_older_than_mins: int
    archive_max_fill_fraction: float
    sync_repeat_time_mins: float
    rsync_opts: str

    @property
    def do_archive(self):
        return True

    @property
    def _archive_dir_local(self):
        return os.path.join(
            os.path.dirname(self.source),
            os.path.basename(self.source) + "_ARCHIVE",
        )

    @property
    def archive_dir(self):
        archive_dir = self._archive_dir
        if not os.access(archive_dir, os.W_OK):
            try:
                os.makedirs(archive_dir, exist_ok=True)
            except Exception:
                archive_dir = self._archive_dir_local
                try:
                    os.makedirs(archive_dir, exist_ok=True)
                except Exception:
                    self.do_archive = False
                    print("Could not archive.")

        return archive_dir

    def archive_file(self, filename, compress_level_int=7):
        zipfile_name = date.today().strftime("%Y%j") + ".zip"
        zipfile_path = os.path.join(self.archive_dir, zipfile_name)
        if self.do_archive:
            z = ZipFile(zipfile_path, "a", ZIP_DEFLATED,
                        compresslevel=compress_level_int)
            z.write(filename)
            z.close()
            os.remove(filename)

    def app_cleanup(self):
        archive_usage = disk_usage(self.archive_dir)
        while (archive_usage.used / archive_usage.total) > \
                self.archive_max_fill_fraction:
            archive_file_pattern = os.path.join(
                self.archive_dir, "???????.zip")
            files = glob(f'{archive_file_pattern}')
            files.sort(key=os.path.getmtime, reverse=True)
            if len(files) > 0:
                os.remove(files.pop())
            else:
                print("Ran out of archive files to remove")
                break

    def __post_init__(self, **kwargs):
        self.source = os.path.normpath(self.source)
        self._archive_dir = os.path.normpath(self._archive_dir)

        if not os.path.isabs(self.source) or not \
                os.path.isabs(self._archive_dir):
            raise ValueError(
                "source and archive dir must not be relative directories. ")
        if not isinstance(self.archive_older_than_mins, int):
            raise TypeError("archive_older_than_mins must be int")
        if (self.archive_max_fill_fraction > ARCHIVE_MAX_FILL_FRACTION_MAX) or \
                (self.archive_max_fill_fraction < ARCHIVE_MAX_FILL_FRACTION_MIN):
            raise ValueError(
                f"archive_max_fill_fraction should be between"
                f"{ARCHIVE_MAX_FILL_FRACTION_MIN} and "
                f"{ARCHIVE_MAX_FILL_FRACTION_MAX}")
        if self.archive_older_than_mins < 0:
            raise ValueError(
                "archive_older_than_mins must be positive integer")
        if os.path.dirname(self.source) == self.source:
            raise ValueError("source cannot be a root directory.")


def parse_config(config_file):
    with open(config_file) as json_file:
        config = Config(**json_load(json_file))
        return config


def app_setup(config_file):
    config = parse_config(config_file)
    config.app_cleanup()
    return config


def rsync_upload_file(filename, destination, rsync_opts, source):

    relative_path = os.path.relpath(filename, source)
    remote_path = (
        destination.rstrip("/") + "/" +
        relative_path.replace(os.sep, "/")
    )

    # Create a temporary snapshot outside the observation directory
    with tempfile.TemporaryDirectory(prefix="ceilometer_sync_") as temp_dir:

        snapshot = os.path.join(temp_dir, os.path.basename(filename))

        # Copy live file to temporary snapshot
        shutil.copyfile(filename, snapshot)

        # Upload snapshot instead of live file
        result = subprocess.run(
            [
                "rclone",
                "copyto",
                snapshot,
                remote_path,
                "--retries", "3",
                "--low-level-retries", "5"
            ],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise ValueError(
                f"Dropbox upload failed: {result.stderr}"
            )

        print(
            f"Uploaded {filename} -> {remote_path}",
            flush=True
        )


def file_age(filename):
    file_ctime = os.path.getmtime(filename)
    file_age_mins = (time() - file_ctime) / 60
    return file_age_mins


def delete_empty_src_directories(source_dir):
    for root, dirs, files in os.walk(os.path.join(source_dir + '')):
        if not os.listdir(root) and not root == source_dir:
            os.rmdir(root)


def sync_files(config):
    for path, folders, files in os.walk(config.source):
        for file in files:
            filename = os.path.join(path, file)
            try:
                sync_file(filename, config)
            except ValueError as e:
                print(e)

    if config.delete_empty_dirs:
        try:
            delete_empty_src_directories(config.source)
        except ValueError as e:
            print(f'Delete dirs failed. {e}')

def is_file_complete(filename):
    with open(filename, "rb") as f:
        f.seek(max(0, os.path.getsize(filename) - 512))
        return b"-File closed:" in f.read()

def sync_file(filename, config):

    print(f"Uploading {filename}", flush=True)

    rsync_upload_file(
        filename,
        config.destination,
        config.rsync_opts,
        config.source
    )

    if (
        file_age(filename) > config.archive_older_than_mins
        and is_file_complete(filename)
    ):
        print(f"Archiving {filename}", flush=True)
        config.archive_file(filename)
        config.app_cleanup()


if __name__ == "__main__":
    parser = ArgumentParser(
        description='Sync data to remote server and do local backup.')
    parser.add_argument(
        '--config_file', help='Directory to configuration file', type=str,
        default="sync_config.json")

    args = parser.parse_args()
    repeat_time_wait = 0
    while True:
        # print(f'sleeping for {repeat_time_wait} minutes')
        sleep(repeat_time_wait * 60)
        time_start = datetime.now()
        config = app_setup(args.config_file)
        sync_files(config)
        time_taken = (datetime.now() - time_start).total_seconds()
        repeat_time_wait = config.sync_repeat_time_mins - (time_taken / 60)
        if repeat_time_wait < 0:
            repeat_time_wait = 0
