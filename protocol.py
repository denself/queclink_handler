import contextlib
from collections import namedtuple, OrderedDict

from voluptuous import Schema, Length, Match, All

from commons.exceptions import *
import conf
import utils

rsrvd = utils.rsrvd
qq = utils.protocol_validator

LOG_MESSAGE = namedtuple('LogMessage', ('type', 'header', 'log'))
OBD_REPORT_MASK = (
    'vin', 'obd_connect', 'obd_power_voltage', 'supported_pids',
    'rpm', 'speed_obd', 'engine_coolant_temp', 'fuel_consumption',
    'DTCs_cleared_distance', 'MIL_active_distance', 'MIL_status',
    'DTCs_cnt', 'DTCs', 'throttle_pos', 'engine_load', 'fuel_level_input',
    rsrvd(), rsrvd(), rsrvd(), rsrvd(), 'gps', 'gsm', 'mileage',
    rsrvd(), rsrvd(), rsrvd(), rsrvd(), rsrvd(),
    rsrvd(), rsrvd(), rsrvd(), rsrvd(),)

GPS_REPORT_INFO = ('gps_accuracy', 'speed', 'heading', 'altitude',
                   'longitude', 'latitude', 'gps_utc_time')

GSM_REPORT_INFO = ('mcc', 'mnc', 'lac', 'cell_id', rsrvd())

PROTO_PASSWORD_SCHEMA = qq('gv500',
                           All(Length(4, 6), Match(r'^[0-9a-zA-Z]+$')))
PROTO_TIME = qq('0000', Length(4))
PROTO_DATE = All(Match(r'^[\d]+$'), Length(min=14, max=14))
PROTO_FLAG = lambda deflt: qq(deflt, Match(r'^[01]$'))


class CommanderMixin(object):

    PREFIX = conf.COMMAND

    GPRS_CFG_RESERVED = [4, 5, 6, 7]
    GPRS_CFG_CMD_SCHEMA = Schema(OrderedDict([
        ('password', PROTO_PASSWORD_SCHEMA),
        ('apn', Length(1, 39)),
        ('apn_user_name', Length(0, 30)),
        ('apn_password', Length(0, 30)),
        ('serial_number', Length(4))
    ]))

    COMMUN_CFG_RESERVED = [2, 12, 13, 14]
    COMMUN_CFG_CMD_SCHEMA = Schema(OrderedDict([
        ('password', PROTO_PASSWORD_SCHEMA),
        ('report_mode', qq('0', Match(r'^[0-6]$'))),
        ('buffer_mode', qq('1', Match(r'^[0-2]$'))),
        ('main_server_ip', Length(0, 60)),
        ('main_server_port', Length(0, 5)),
        ('backup_server_ip', Length(0, 60)),
        ('backup_server_port', Length(0, 5)),
        ('sms_gateway', Length(0, 20)),
        ('heartbeat_interval', qq('0', Length(1, 3))),
        ('sack_enable', PROTO_FLAG('0')),
        ('protocol_format', PROTO_FLAG('0')),
        ('serial_number', Length(4))
    ]))

    FIXED_REPORT_CFG_RESERVED = [3, 7, 11, 14, 15, 16, 17]
    FIXED_REPORT_CFG_SCHEMA = Schema(OrderedDict([
        ('password', PROTO_PASSWORD_SCHEMA),
        ('mode', qq('0', Match(r'^[0-4]$'))),
        ('discard_no_fix', PROTO_FLAG('1')),
        ('period_enable', PROTO_FLAG('1')),
        ('start_time', PROTO_TIME),
        ('end_time', PROTO_TIME),
        ('send_interval', qq('30', Length(max=5))),
        ('distance', qq('1000', Length(max=5))),
        ('mileage', qq('1000', Length(max=5))),
        ('corner_report', qq('0', Length(max=3))),
        ('ign_report_interval', qq('600', Length(max=5))),
        ('serial_number', Length(4))
    ]))

    OBD_REPORT_CFG_RESERVED = [11, 12, 13, 14]
    OBD_REPORT_CFG_SCHEMA = Schema(OrderedDict([
        ('password', PROTO_PASSWORD_SCHEMA),
        ('mode', PROTO_FLAG('1')),
        ('obd_check_interval', qq('30', Length(max=5))),
        ('obd_report_interval', qq('0', Length(max=5))),
        ('obd_report_interval_igf', qq('0', Length(max=5))),
        ('obd_report_mask', qq('FFFF', Length(max=8))),
        ('obd_event_mask', qq('3', Length(max=4))),
        ('displacement', qq('2.0', Length(max=4))),
        ('fuel_oil_type', qq('2', Length(max=3))),
        ('custom_fuel_ratio', qq('14.3', Length(max=4))),
        ('custom_fuel_density', qq('0.737', Length(max=5))),
        ('serial_number', Length(4))
    ]))

    TIME_ADJ_CFG_RESERVED = [6, 7, 8, 9]
    TIME_ADJ_CFG_SCHEMA = Schema(OrderedDict([
        ('password', PROTO_PASSWORD_SCHEMA),
        ('sign', qq('+', Match(r'^[-+]$'))),
        ('hour_offset', qq('0', All(Match(r'^[\d]+$'), Length(max=2)))),
        ('minute_offset', qq('0', All(Match(r'^[\d]+$'), Length(max=2)))),
        ('daylight_saving', PROTO_FLAG('0')),
        ('utc_time', PROTO_DATE),
        ('serial_number', Length(4))
    ]))

    RTO_CFG_RESERVED = [3, 4, 5, 6]
    RTO_CFG_SCHEMA = Schema(OrderedDict([
        ('password', PROTO_PASSWORD_SCHEMA),
        ('sub_cmd', Match(r'^[0-9ABC]$')),
        ('at_cmd', qq('', Length(min=0, max=3))),
        ('serial_number', Length(4))
    ]))

    def build_cmd(self, cmd, **kv):
        kv = self.serialize_params(kv)
        if not cmd in conf.COMMANDS:
            raise MessageNotImplemented(
                "Command is not registered: %s" % cmd)
        cmder = getattr(self, 'build_{}_params'.format(cmd.lower()), None)
        if not cmder or not callable(cmder):
            raise MessageNotImplemented(
                "Command is not implemented: %s" % cmd)
        params = cmder(**kv)
        return self.message_builder(conf.COMMAND, cmd, *params)

    def build_bsi_params(self, **kv):
        return self.__build_params(self.GPRS_CFG_CMD_SCHEMA,
                                   self.GPRS_CFG_RESERVED,
                                   kv)

    def build_sri_params(self, **kv):
        return self.__build_params(self.COMMUN_CFG_CMD_SCHEMA,
                                   self.COMMUN_CFG_RESERVED,
                                   kv)

    def build_fri_params(self, **kv):
        return self.__build_params(self.FIXED_REPORT_CFG_SCHEMA,
                                   self.FIXED_REPORT_CFG_RESERVED,
                                   kv)

    def build_tma_params(self, **kv):
        return self.__build_params(self.TIME_ADJ_CFG_SCHEMA,
                                   self.TIME_ADJ_CFG_RESERVED,
                                   kv)

    def build_rto_params(self, **kv):
        return self.__build_params(self.RTO_CFG_SCHEMA,
                                   self.RTO_CFG_RESERVED,
                                   kv)

    def build_obd_params(self, **kv):
        if 'obd_report_mask' in kv:
            mask = kv['obd_report_mask']
            calc_mask = 0
            for cur_mask_item in mask:
                found = -1
                for i, mask_item in enumerate(OBD_REPORT_MASK):
                    if mask_item == cur_mask_item:
                        found = i
                if found == -1:
                    raise MessageFormatException(
                        "wrong item in OBD report mask: %s" % cur_mask_item)
                calc_mask |= (1 << found)
            kv['obd_report_mask'] = hex(calc_mask).lstrip('0x').upper()

        return self.__build_params(self.OBD_REPORT_CFG_SCHEMA,
                                   self.OBD_REPORT_CFG_RESERVED,
                                   kv)

    def __build_params(self, schema, reserved, kv):
        _fields = schema.schema.keys()
        _vals = [kv.get(f, '') for f in _fields]
        _rv = schema(dict(zip(_fields, _vals)))
        _vals = [_rv.get(f) for f in _fields]
        params_cnt = len(_vals) + len(reserved)
        params = [''] * params_cnt
        blocked_cnt, val_cnt = 0, 0
        for i in range(params_cnt):
            if len(reserved) > blocked_cnt:
                if reserved[blocked_cnt] == i:
                    blocked_cnt += 1
                    continue
            params[i] = _vals[val_cnt]
            val_cnt += 1
        return tuple(params)

    def sack(self, cmd, msg):
        return self.message_builder(conf.SACK, cmd,
                                    msg.log.count_number,)


class AcknowledgerMixin(object):
    GeneralAck = namedtuple(
        'GeneralAck', (
            'protocol_version', 'unique_id', 'device_name',
            'serial_number', 'send_time', 'count_number'))
    HeartbeatAck = namedtuple(
        'HeartbeatAck', (
            'protocol_version', 'unique_id', 'device_name',
            'send_time', 'count_number'))

    RTOAck = namedtuple(
        'RTOAck', (
            'protocol_version', 'unique_id', 'device_name',
            'sub_cmd', 'serial_number', 'send_time', 'count_number'))

    def ack(self, msg_type, *params):
        if not msg_type in conf.ACKS:
            raise MessageNotImplemented(
                "Ack is not registered: %s" % msg_type)
        acker = getattr(self, 'ack_{}'.format(msg_type.lower()), None)
        if not acker or not callable(acker):
            raise MessageNotImplemented(
                "Message is not implemented: %s" % msg_type)
        msg = acker(*params)
        sack = self.message_builder(
            conf.SACK,
            msg_type,
            msg.log.protocol_version,
            msg.log.count_number)
        return (msg, sack)

    def ack_hbd(self, *params):
        ack_msg = self.HeartbeatAck._make(params)
        return LOG_MESSAGE._make((conf.ACK, conf.HEARTBEAT_ACK, ack_msg))

    def ack_rto(self, *params):
        ack_msg = self.RTOAck._make(params)
        return LOG_MESSAGE._make((conf.ACK, conf.RTO_ACK, ack_msg))

    def ack_sri(self, *params):
        return self.__ack_general(conf.COMMUN_CONFIG_ACK, *params)

    def ack_fri(self, *params):
        return self.__ack_general(conf.FIXED_REPORT_ACK, *params)

    def __ack_general(self, header, *params):
        ack_msg = self.GeneralAck._make(params)
        return LOG_MESSAGE._make((conf.ACK, header, ack_msg))


class ReportProcessor(object):

    def __init__(self, *a, **kwargs):
        self.require_ack = kwargs.get('require_ack', False)
        self.cur_mode = conf.REPORT

    FixedReport = namedtuple(
        'FixedReport', (
            'protocol_version', 'unique_id', 'vin', 'device_name',
            'external_power_voltage', 'report_id', 'number', 'gps_accuracy',
            'speed', 'heading', 'altitude', 'longitude', 'latitude',
            'gps_utc_time', 'mcc', 'mnc', 'lac', 'cell_id', rsrvd(),
            'mileage', 'hour_meter_count', rsrvd(), rsrvd(),
            'backup_battery_percentage', 'device_status', 'rpm',
            'fuel_consumption', 'fuel_level_input', 'send_time',
            'count_number',))

    FixedReportBicycle = namedtuple(
            'FixedReportBicycle', (
            'protocol_version', 'unique_id', 'device_name', 'external_power_voltage',
            'report_id', 'number', 'gps_accuracy', 'speed', 'azimuth', 'altitude',
            'longitude', 'latitude', 'gps_utc_time', 'mcc', 'mnc', 'lac', 'cell_id',
            rsrvd(), 'mileage', 'hour_meter_count', 'analog_input_vcc', rsrvd(),
            rsrvd(), 'device_status', rsrvd(), rsrvd(), rsrvd(), 'send_time', 'count_number'))

    DeviceInformationReport = namedtuple(
        'DeviceInformationReport', (
            'protocol_version', 'unique_id', 'vin', 'device_name',
            'state', 'iccid', 'csq_rssi', 'csq_ber', 'external_power_supply',
            'external_power_voltage', rsrvd(), 'backup_battery_voltage',
            'charging', 'led_on', rsrvd(), rsrvd(), 'last_fixed_utc_time',
            rsrvd(), rsrvd(), rsrvd(), rsrvd(), rsrvd(), 'tz_offset',
            'daylight_saving', 'send_time', 'count_number'))

    MotionStateReport = namedtuple(
        'MotionStateReport', (
            'protocol_version', 'unique_id', 'vin', 'device_name',
            'state', 'gps_accuracy', 'speed', 'heading', 'altitude',
            'longitude', 'latitude', 'gps_utc_time', 'mcc',
            'mnc', 'lac', 'cell_id', rsrvd(), 'send_time', 'count_number',))

    VersionReport = namedtuple(
        'VersionReport', (
            'protocol_version', 'unique_id', 'vin', 'device_name',
            'device_type', 'sw_version', 'hw_version',
            'send_time', 'count_number'))

    def process_message(self, msg_type, *params, **kw):
        r"""Facade method that calls corresponding report processor."""
        from_buffer = kw.get('from_buffer', False)
        if not msg_type in conf.REPORTS:
            raise MessageNotImplemented(
                "Message is not registered: %s" % msg_type)
        cb = getattr(self, 'process_{}_report'.format(msg_type.lower()), None)

        if not cb or not callable(cb):
            raise MessageNotImplemented(
                "Message is not implemented: %s" % msg_type)
        if from_buffer:
            with self.buffer_ctx():
                report = cb(*params)
        else:
            report = cb(*params)
        sack = self.sack(msg_type, report)
        return (report, sack)

    def process_fri_report(self, *params):
        r"""Callback, that returns fixed report"""
        params = list(params)
        if params[0] == '210501':
            return self.process_fri_bicycle_report(*params)
        NUMBER_OF_GPS_IDX = 6
        GPS_INFO_PARAMS = 12
        number_of_gps = int(params[NUMBER_OF_GPS_IDX])
        if number_of_gps > 1:
            from_idx = NUMBER_OF_GPS_IDX + 1
            to_idx = GPS_INFO_PARAMS + from_idx
            omit_cnt = GPS_INFO_PARAMS * (number_of_gps - 1)
            params = params[:to_idx] + params[to_idx + omit_cnt:]

        report = self.FixedReport._make(params)
        return LOG_MESSAGE._make((self.cur_mode, conf.FIXED_REPORT, report))

    def process_fri_bicycle_report(self, *params):
        NUMBER_OF_GPS_IDX = 5
        GPS_INFO_PARAMS = 12
        params = list(params)
        number_of_gps = int(params[NUMBER_OF_GPS_IDX])
        if number_of_gps > 1:
            from_idx = NUMBER_OF_GPS_IDX + 1
            to_idx = GPS_INFO_PARAMS + from_idx
            omit_cnt = GPS_INFO_PARAMS * (number_of_gps - 1)
            params = params[:to_idx] + params[to_idx + omit_cnt:]

        report = self.FixedReportBicycle._make(params)
        return LOG_MESSAGE._make((self.cur_mode, conf.FIXED_REPORT, report))

    def process_obd_report(self, *params):
        OBDStaticReport = namedtuple('OBDStaticReport', (
            'protocol_version', 'unique_id', 'gps_vin', 'device_name',
            'report_type', 'report_mask'))

        obd_rep_len = len(OBDStaticReport._fields)
        obd_report = OBDStaticReport._make(params[:obd_rep_len])
        obd_mask = int(obd_report.report_mask, 16)
        more_fields = []
        for i in range(0, len(OBD_REPORT_MASK)):
            if (1 << i) & obd_mask:
                if OBD_REPORT_MASK[i] == 'gps':
                    more_fields.extend(GPS_REPORT_INFO)
                elif OBD_REPORT_MASK[i] == 'gsm':
                    more_fields.extend(GSM_REPORT_INFO)
                else:
                    more_fields.append(OBD_REPORT_MASK[i])
        # TODO. temporary hotfix until queclink will answer
        try:
            more_fields.extend(('send_time', 'count_number'))
            report = namedtuple('OBDReport',
                                OBDStaticReport._fields + tuple(more_fields))
            report = report._make(params)
        except TypeError:
            more_fields.pop()
            more_fields.pop()
            more_fields.extend((rsrvd(), 'send_time', 'count_number'))
            report = namedtuple('OBDReport',
                                OBDStaticReport._fields + tuple(more_fields))
            report = report._make(params)
        return LOG_MESSAGE._make((self.cur_mode, conf.OBD_REPORT, report))

    def process_stt_report(self, *params):
        report = self.MotionStateReport._make(params)
        return LOG_MESSAGE._make((self.cur_mode,
                                 conf.MOTION_STATE_REPORT, report))

    def process_inf_report(self, *params):
        report = self.DeviceInformationReport._make(params)
        return LOG_MESSAGE._make((self.cur_mode,
                                 conf.DEVICE_INFORMATION_REPORT, report))

    def process_ver_report(self, *params):
        report = self.VersionReport._make(params)
        return LOG_MESSAGE._make((self.cur_mode,
                                 conf.VER_REPORT, report))

    @contextlib.contextmanager
    def buffer_ctx(self):
        self.cur_mode = conf.BUFF
        yield
        self.cur_mode = conf.REPORT


class QueclinkProtocol(CommanderMixin,
                       ReportProcessor,
                       AcknowledgerMixin):

    def __init__(self, *a, **kw):
        super(QueclinkProtocol, self).__init__(*a, **kw)

    def terminal_message_flow(self, msg):
        r"""Dictates message flow in protocol.
        Returns tuple of: (msg:LOG_MESSAGE, sack:str)"""
        self.message_validator(msg)
        msg = msg.rstrip(conf.END_SIGN)
        pprocessor, msg_tp, params, kw = self.message_parser(msg)
        log, sack = pprocessor(msg_tp, *params, **kw)
        return log, sack, kw.get('from_buffer', False)

    def message_validator(self, msg):
        if not msg.endswith(conf.END_SIGN):
            raise BadProtocolFormat(conf.MESSAGE_SHOULD_END_EXC)
        ok = False
        for msg_tp in conf.MESSAGES:
            if msg.startswith(msg_tp):
                ok = True
        if not ok:
            raise BadProtocolFormat(conf.MESSAGE_SHOULD_BE_IN_EXC)

    def message_parser(self, msg):
        if msg.startswith(conf.REPORT) or msg.startswith(conf.BUFF):
            is_buff = None
            if msg.startswith(conf.REPORT):
                msg = msg[len(conf.REPORT):]
            else:
                msg = msg[len(conf.BUFF):]
                is_buff = True
            report, paramstring = msg.split(',', 1)
            return (self.process_message, report, paramstring.split(','),
                    {'from_buffer': is_buff})
        elif msg.startswith(conf.ACK):
            ack, paramstring = msg[len(conf.ACK):].split(',', 1)
            return (self.ack, ack, paramstring.split(','), {})
        else:
            raise BadProtocolFormat(conf.UNKNOWN_MESSAGE % msg)

    def message_builder(self, msg_type, command, *params):
        msgstr = ''
        header = msg_type + command
        paramstring = ','.join(params)
        if command in (conf.ACK, conf.REPORT):
            msgstr = header + ',' + paramstring
        else:
            msgstr = header + '=' + paramstring
        msgstr += conf.END_SIGN
        self.message_validator(msgstr)
        return msgstr

    def serialize_params(self, kv):
        params = {}
        for k, v in kv.iteritems():
            if not isinstance(v, (list, tuple)):
                if isinstance(v, bool):
                    params[k] = str(int(v))
                else:
                    params[k] = str(v)
            else:
                params[k] = v
        return params
