MESSAGES = (COMMAND, ACK, REPORT, SACK, BUFF) = (
    'AT+GT', '+ACK:GT', '+RESP:GT', '+SACK:GT', '+BUFF:GT')
END_SIGN = '$'
RESERVED = 'x'
RESERVED_VAL = ''
# commands
GPRS_CONFIG_CMD = 'BSI'
COMMUN_CONFIG_CMD = 'SRI'
FIXED_REPORT_CMD = 'FRI'
OBD_REPORT_CMD = 'OBD'
TIME_ADJST_CMD = 'TMA'
RTO_CMD = 'RTO'

RTO_SUB_CMDS = (RTO_VER,) = (8,)
# reports
FIXED_REPORT = 'FRI'
OBD_REPORT = 'OBD'
DEVICE_INFORMATION_REPORT = 'INF'
MOTION_STATE_REPORT = 'STT'  # if motion state changed
VER_REPORT = 'VER'  # version info report
# acks
HEARTBEAT_ACK = 'HBD'
COMMUN_CONFIG_ACK = 'SRI'
FIXED_REPORT_ACK = 'FRI'
RTO_ACK = 'RTO'

REPORTS = (FIXED_REPORT, OBD_REPORT, MOTION_STATE_REPORT,
           DEVICE_INFORMATION_REPORT, VER_REPORT)
ACKS = (HEARTBEAT_ACK, COMMUN_CONFIG_ACK, FIXED_REPORT_ACK, RTO_ACK)
COMMANDS = (GPRS_CONFIG_CMD, COMMUN_CONFIG_CMD, TIME_ADJST_CMD,
            FIXED_REPORT_CMD, OBD_REPORT_CMD, RTO_CMD)

MESSAGE_SHOULD_END_EXC = "Message should end on char '$'."
MESSAGE_SHOULD_BE_IN_EXC = "Message should be `+ACK:GT`, `+RESP:GT`"
UNKNOWN_MESSAGE = "Message %s is unknown to the protocol."

TCP_LONG_CONN = 3
BUFF_HIGH_PRIORITY = 2
DEFAULT_HEARTBEAT = 15          # seconds
ASCII_FORMAT = 0
FIXED_TIMING_REPORT_MODE = 1

DISCONN_RESULT = 'disconnect'
