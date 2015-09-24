from tornado import gen
import conf
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
        if self.config['sack_enable']:
            # TODO. logic to sack
            pass
        mapped_log = {}
        mapped_log['imei'] = log.get('unique_id', self.session_key)
        mapped_log['device_tp'] = obd.QUECLINK
        mapped_log['vin'] = log.get('vin', None)
        if not mapped_log['vin'] is None:
            mapped_log['vin'] = mapped_log['vin'].decode('utf-8', 'ignore')
        mapped_log['from_buffer'] = from_buffer
        try:
            mapped_log['gps_utc_time'] = time_utils.dt2ts(time_utils.to_dt(
                log.get('gps_utc_time')))
        except (ValueError, TypeError):
            return

        mapped_log['ts'] = mapped_log['gps_utc_time']
        if response.header == conf.FIXED_REPORT:
            if log.get('protocol_version') == '210501':  # bicycle
                mapped_log['gps_accuracy'] = log.get('gps_accuracy', None)
                mapped_log['speed'] = log.get('speed', None)
                mapped_log['altitude'] = log.get('altitude', None)
                mapped_log['longitude'] = log.get('longitude', None)
                mapped_log['latitude'] = log.get('latitude', None)
                mapped_log['mileage'] = log.get('mileage', None)
            else:
                mapped_log['gps_accuracy'] = log.get('gps_accuracy', None)
                mapped_log['speed'] = log.get('speed', None)
                mapped_log['altitude'] = log.get('altitude', None)
                mapped_log['longitude'] = log.get('longitude', None)
                mapped_log['latitude'] = log.get('latitude', None)
                mapped_log['mileage'] = log.get('mileage', None)
                mapped_log['rpm'] = log.get('rpm', None)
                mapped_log['fuel_consumption'] = log.get('fuel_consumption', None)
                mapped_log['fuel_level_input'] = log.get('fuel_level_input', None)
        elif response.header == conf.OBD_REPORT:
            mapped_log['obd_connect_status'] = int(log.get('obd_connect', '0'))
            mapped_log['power_voltage'] = log.get('obd_power_voltage', None)
            mapped_log['supported_pids'] = utils.process_supported_pids(
                log.get('supported_pids', '00000000'))
            mapped_log['rpm'] = log.get('rpm', None)
            mapped_log['engine_coolant_temp'] = log.get(
                'engine_coolant_temp', None)
            mapped_log['fuel_consumption'] = log.get(
                'fuel_consumption', None)
            mapped_log['DTCs_cleared_distance'] = log.get(
                'DTCs_cleared_distance', None)
            mapped_log['MIL_active_distance'] = log.get(
                'MIL_active_distance', None)
            mapped_log['MIL_status'] = int(log.get('MIL_status') or '0')
            mapped_log['DTCs_number'] = int(log.get('DTCs_cnt') or '0')
            mapped_log['DTCs'] = extract_codes(
                mapped_log['DTCs_number'], log.get('DTCs', None))
            mapped_log['throttle_position'] = log.get('throttle_pos', None)
            mapped_log['engine_load'] = log.get('engine_load', None)
            mapped_log['fuel_level_input'] = log.get('fuel_level_input', None)
            mapped_log['gps_accuracy'] = log.get('gps_accuracy', None)
            mapped_log['altitude'] = log.get('altitude', None)
            mapped_log['longitude'] = log.get('longitude', None)
            mapped_log['latitude'] = log.get('latitude', None)
            mapped_log['speed'] = log.get('speed', None)
            mapped_log['external_power_voltage'] = log.get('obd_power_voltage', None)
        else:
            gen_log.warning("Common Protocol hasn't conform to report %s",
                            response.header)
        if mapped_log:
            #raise Exception(mapped_log)
            mapped_log = COMMON_LOG_SCHEMA(mapped_log)

            # TODO: save to postgres
            # redis_conn.publish(redis_keys.OBD_LOG_CHANNEL,
            #                    protocol.dump_msg(mapped_log))

            gen_log.info('MESSAGE PUBLISHED %s', mapped_log)
            raise gen.Return(mapped_log)
        gen_log.info("PROCESSED REPORT: %s[ack-%s]", log, sack)
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
