import os
from pathlib import Path


def file_exists(file_path):
    '''Returns if file exists or not.'''
    file_path = Path(file_path)
    return file_path.exists()


def file_size_in_bytes(file_path):
    '''Return size of file in bytes, or -1 if file does not exist.'''
    if not file_exists(file_path):
        return -1
    statinfo = os.stat(file_path)
    return int(statinfo.st_size)


MAX_FILE_SIZE_FOR_PUT_API = int(1024 * 1024 * 4)


def files_must_not_be_more_than(files, file_size_limit_in_bytes):
    '''
    Guards against files with size exceeding a limit being attempted.
    Returns a tuple (int bytes_over_limit, bool error)
    '''
    file_size_limit_in_bytes = int(file_size_limit_in_bytes)
    total_bytes = 0
    for current_file in files:
        current_file_size_in_bytes = file_size_in_bytes(current_file)

        if current_file_size_in_bytes < 0:
            return (0, True, )

        total_bytes = total_bytes + int(current_file_size_in_bytes)

        if total_bytes > file_size_limit_in_bytes - 1:
            return (total_bytes - file_size_limit_in_bytes, True, )

    return 0, False
