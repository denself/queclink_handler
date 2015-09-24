import logging

# gen logger
app_logger = logging.getLogger('mobiliuz.queclink')
app_logger.setLevel(logging.INFO)
consoleh = logging.StreamHandler()
formatter = logging.Formatter('[%(asctime)s]   IMEI#%(imei)s       %(msgtype)s---%(message)-4s', '%Y-%m-%d %H:%M:%S')
consoleh.setFormatter(formatter)
app_logger.addHandler(consoleh)
app_logger.propagate = False

# gen logger
gen_logger = logging.getLogger('mobiliuz.queclink.general')
gen_logger.setLevel(logging.INFO)
gen_consoleh = logging.StreamHandler()
gen_formatter = logging.Formatter('[%(asctime)s]    %(message)-4s', '%Y-%m-%d %H:%M:%S')
gen_consoleh.setFormatter(gen_formatter)
gen_logger.addHandler(gen_consoleh)
gen_logger.propagate = False

monitor_logger = logging.getLogger('mobiliuz.queclink.monitor')
monitor_logger.setLevel(logging.INFO)
gen_consoleh = logging.StreamHandler()
gen_formatter = logging.Formatter('[%(asctime)s] %(monitor)s::::%(message)-4s', '%Y-%m-%d %H:%M:%S')
gen_consoleh.setFormatter(gen_formatter)
monitor_logger.addHandler(gen_consoleh)
monitor_logger.propagate = False



app_log = app_logger
gen_log = gen_logger
monitor_log = monitor_logger
