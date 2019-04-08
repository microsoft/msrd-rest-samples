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


def files_must_not_be_more_than(files, limit):
    '''
    Guards against files with size exceeding a limit being attempted.
    Returns a tuple (int bytes_over_limit, bool error)
    '''
    limit = int(limit)
    total = 0
    for file in files:
        bytes = file_size_in_bytes(file)

        if bytes < 0:
            return (0, True, )

        total = total + int(bytes)

        if total > limit - 1:
            return (total - limit, True, )

    return 0, False
