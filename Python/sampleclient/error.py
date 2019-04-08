
def error_out(log, error_string):
    '''Log an explicit error and exit the application.'''
    if log and error_string:
        log.error(error_string)
    exit(1)
