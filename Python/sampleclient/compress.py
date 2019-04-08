import shutil
from .error import error_out


def create_archive(log, src_dir, archive_base_name):
    """
    Create a compressed .zip archive of a directory.

    Args:
        src_dir: Path to the directory to archive. This will be the root of the
            resulting archive.
        archive_base_name: The name of the resulting archive. For example, an
            argument of "data" will result in an archive named "data.zip".
    """

    # Get a generator of names of supported archive formats.
    archive_formats = (fmt for (fmt, _) in shutil.get_archive_formats())

    # We could use other formats, but just require `zip` for now.
    if 'zip' not in archive_formats:
        error_out(log, 'Unable to create `.zip` files, aborting.')

    log.debug(
        'Creating zip archive with base name `%s` and root dir `%s`.',
        archive_base_name,
        src_dir,
    )

    # The archive will be created in the working directory, and we return the
    # full name (including extension) of the created file.
    return shutil.make_archive(archive_base_name, 'zip', logger=log, root_dir=src_dir)
