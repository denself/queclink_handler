from tornado import gen
import conf
from models import Backend, LogEntry
import utils
from logger import gen_log
from commons.schemas import COMMON_LOG_SCHEMA
from commons import obd
from commons import utils as time_utils

DEFAULT_CONFIGURATIONS = {
    'password': '',
    'apn': '',
    'report_mode': conf.TCP_LONG_CONN,
    'main_server_ip': '',
    'main_server_port': '',
    'backup_server_ip': '',
    'backup_server_port': '',
    'sms_gateway': '',
    'heartbeat_interval': 15,
    'sack_enable': False,
    'protocol_format': conf.ASCII_FORMAT,
    'send_interval': 30,
    'fixed_report_mode': conf.FIXED_TIMING_REPORT_MODE
}


def extract_codes(dtc_number, raw_codes):
    DTC_CODE_CONVERSION = {
        '0': 'P0',
        '1': 'P1',
        '2': 'P2',
        '3': 'P3',
        '4': 'C0',
        '5': 'C1',
        '6': 'C2',
        '7': 'C3',
        '8': 'B0',
        '9': 'B1',
        'A': 'B2',
        'B': 'B3',
        'C': 'U0',
        'D': 'U1',
        'E': 'U2',
        'F': 'U3'
    }

    if not dtc_number:
        return ''

    dtcs, j = [], 0
    for i in range(0, dtc_number):
        raw_code = raw_codes[j:j + 4]
        dtc_code = DTC_CODE_CONVERSION[raw_code[0]] + raw_code[1:]
        dtcs.append(dtc_code)
        j += 4
    return obd.DTC_CODE_SPLITTER.join(dtcs)


class QueclinkConnection(object):

    r"""High level terminal connection."""

    default_mil_interval = 60 * 5

    def __init__(self, session, **kwargs):
        self._session = session
        self.__imei = None
        self.serial_number = '0000'
        self.config = DEFAULT_CONFIGURATIONS.copy()
        self.config.update(kwargs)

    @property
    def backend(self):
        return Backend.instance()

    @property
    def is_auth(self):
        return self._session.is_open()

    @property
    def io_loop(self):
        return self._session.io_loop

    @property
    def session_key(self):
        return self._session.session_key

    @gen.coroutine
    def on_open(self, imei):
        r"""Callback that signifies that connection is open"""
        self.__imei = imei
        msg = {'imei': imei,
               'conn_status': 1,
               'ts': str(time_utils.now())}

    @gen.coroutine
    def on_report(self, original_msg, response, sack, from_buffer=False):
        log = dict(response.log.__dict__)

        log_entry = LogEntry()

        log_entry.imei = log.get('unique_id', self.session_key)

        try:
            log_entry.gps_utc_time = time_utils.dt2ts(time_utils.to_dt(
                log.get('gps_utc_time')))
        except (ValueError, TypeError):
            return

        if response.header in (conf.FIXED_REPORT, conf.OBD_REPORT):
            log_entry.gps_accuracy = log.get('gps_accuracy', None)
            log_entry.speed = log.get('speed', None)
            log_entry.altitude = log.get('altitude', None)
            log_entry.longitude = log.get('longitude', None)
            log_entry.latitude = log.get('latitude', None)
            # mapped_log['rpm'] = log.get('rpm', None)
        else:
            gen_log.warning("Common Protocol hasn't conform to report %s",
                            response.header)
            raise gen.Return(None)
        session = self.backend.get_session()

        try:
            """Everything I need to do here"""
            session.add(log_entry)
            session.commit()
        except Exception as e:
            session.rollback()
        finally:
            session.close()

        gen_log.info('MESSAGE PUBLISHED %s', log_entry.json())
        raise gen.Return(None)

    @gen.coroutine
    def on_ack(self, original_msg, msg, sack):
        gen_log.info("PROCESSED ACK: %s[ack-%s]", msg, sack)
        if self.config['sack_enable'] or (msg.type == conf.ACK and
                                          msg.header == conf.HEARTBEAT_ACK):
            self._session.send_message(sack)
        raise gen.Return(None)

    def verify_conn(self):
        return self._session.make_rto({'sub_cmd': conf.RTO_VER})

    @gen.coroutine
    def configure(self):
        r"""Executes commands for device configuration.
        Returns unique id if configuration has been successful."""
        pass

    def on_close(self):
        msg = {'imei': self.__imei,
               'conn_status': 0,
               'ts': str(time_utils.now())}
