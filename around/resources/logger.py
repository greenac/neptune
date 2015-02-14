import logging, os, sys, datetime

class Logger:
    def __init__(self, file_name, level=20):
        self.file_name = file_name
        self.level = level
        self.path = '/var/log/' + self.file_name
        self.set_config()

    def set_config(self):
        logging.basicConfig(filename=self.path, level=self.level)
        return None

    def log_message(self, message):
        logging.log(self.level, self.utc_now_string() + ' ' + message)
        return None

    def log_error(self, message):
        exc_type, exc_obj, exc_tb = sys.exc_info()
        file_name = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        error_string = '%s ERROR:%s FILE:%s LINE:%s %s' % (self.utc_now_string(),
                                                           str(exc_type),
                                                           file_name,
                                                           str(exc_tb.tb_lineno),
                                                           message)
        logging.log(self.level, error_string)
        return None

    def utc_now_string(self):
        d = datetime.datetime.utcnow()
        return '[%d-%d-%d %d:%d:%d:%d]' % (d.year, d.month, d.day, d.hour, d.minute, d.second, d.microsecond)