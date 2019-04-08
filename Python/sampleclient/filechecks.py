import os
from pathlib import Path


def file_exists(file_path):
    '''Returns if file exists or not.'''
    file = Path(file_path)
    return file.exists()


def file_size_in_bytes(file_path):
    '''Return size of file in bytes, or -1 if file does not exist.'''
    if not file_exists(file_path):
        return -1
    statinfo = os.stat(file_path)
    return int(statinfo.st_size)


MAX_FILE_SIZE_FOR_PUT_API = int(1024 * 1024 * 4)


def files_must_not_be_more_than(log, files, limit):
    '''Guards against files with size exceeding a limit being attempted.'''
    total = 0
    for file in files:
        bytes = file_size_in_bytes(file)

        if bytes < 0:
            if log:
                log.error(
                    'File %s does not exist.',
                    file
                )
            exit(1)

        total = total + int(bytes)

        if total > MAX_FILE_SIZE_FOR_PUT_API - 1:
            if log:
                log.error(
                    'File %s would exceed the max allowed size by %s bytes.',
                    total - MAX_FILE_SIZE_FOR_PUT_API
                )
            exit(1)
