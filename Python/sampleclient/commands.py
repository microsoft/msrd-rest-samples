import argparse


def parse_args():
    """
    Parse arguments for command-line invocation of the script.
    """

    arg_parser = argparse.ArgumentParser(
        description='Microsoft Security Risk Detection (MSRD) job creation client'
    )

    required_flag_defs = [
        ('--config', 'JSON file containing MSRD client config data'),
        ('--job_path', 'Path to directory of executable and seed data for the MSRD job'),
        ('--job_params', 'JSON file containing job parameters'),
        ('--job_os', 'Operating System type to use. Use "osType" value from os api.'),
        ('--job_os_edition', 'Operating System Edition to use. Use "osEdition" value from os api.'),
    ]

    for flag, flag_help in required_flag_defs:
        arg_parser.add_argument(flag, required=True, help=flag_help)

    arg_parser.add_argument(
        '--storage_type',
        default='AZURE',
        required=True,
        help="""specifies the method of file uplaod for submission of the job. The options are
                - AZURE: The job will leverage Microsoft AZURE Binary Blob Storage.
                - API: The job will leverage the MSDR file upload HTTP/PUT API."""
    )

    arg_parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Use debug-level logging'
    )

    arg_parser.add_argument(
        '--submission_type',
        default='VM',
        help="""specifies the method of submission of the job. The options are
                - VM: The job will provision a preparation machine where the dependencies will be installed before fuzzing.
                - package: The job will bypass the provision of the preparation machine and go directly to the fuzzing step."""
    )

    return arg_parser.parse_args()
