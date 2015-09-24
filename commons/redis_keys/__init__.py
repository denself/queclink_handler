OBD_KEY_NS = 'obd' # key namespace for obd like data

VEHICLE_STATE_KEY = 'obd:carstate#%(imei)s' # intermediate object between park and route

IMEI_FOLDER_OF_TRANSTATES_KEYS = 'obd:transtates*'

SEQUENCE_TRANSTATE_ID = 'obd:transtate_cnt#%s'  # imei

# set of keys of Route or Park objects
SET_OF_TRANSTATES_KEY = 'obd:transtates#%(imei)s'

CAR_DRIVING_TIME_PER_DAY = 'obd:driving_time#%(imei)s_%(date)s'
# provide vehicle imei and (route|park) id
VEHICLE_TRANSTATE_KEY = 'obd:transtate#%(imei)s_%(tid)s'

MOBILIUZ_IMEI_BY_VEHICLE_ID_KEY = 'mobiliuz:imei_by_vehicle:%(vehicle_pk)s'

MOBILIUZ_VEHICLE_ID_BY_IMEI_KEY = 'mobiliuz:vehicle_by_imei:%(imei)s'

MOBILIUZ_VEHICLE_RULES_KEY = 'mobiliuz:vehicle_rules:%(vehicle_pk)s'

MOBILIUZ_USER_TOKEN = 'mobiliuz:token#%(user_pk)s'
MOBILIUZ_TOKEN_USER = 'mobiliuz:user#%(token)s'

DAILY_CAR_VIOLATIONS = 'mobiliuz:violations.%(date)s_%(subscr_pk)s'
DAILY_CAR_MIL_ON = 'mobiliuz:carhealth.%(date)s_%(subscr_pk)s'
DAILY_CAR_MILEAGE = 'mobiliuz:mileage.%(date)s_%(vehicle_pk)s'
CAR_DANGER_ZONE_FLAG = 'mobiliuz:danger_zone.%(date)s_%(subscr_pk)s_%(car_pk)s'
CAR_LAST_LOCATION = 'obd:last_location#%(vehicle_pk)s'
# CAR_NOTIF_FOR_RULE = 'mobiliuz:notified.%(date)s_%(conf_rule_pk)s_%(car_pk)s'
CAR_VIOLATIONS = 'mobiliuz:violations.%(random)s_%(subscr_pk)s'

MOBILIUZ_VEHICLES_KEY = 'mobiliuz:vehicles'

DEVICE_OBD_LOG = 'obd.%(imei)s'
DEVICE_GPS_LOG = 'gps.%(imei)s'

OBD_LOG_CHANNEL = 'obd:log'
TCP_DONGLE_CHANNEL = 'obd:presence'
TCP_DONGLE_LOG = 'obd:log_%s'  # imei
NOTIFICATION_CHANNEL = 'mobiliuz:notif_chnl'

SYNC_TABLE_KEY = 'mobiliuz:configurations'
SYNC_CHANNEL = 'mobiliuz:configurations_chnl'
