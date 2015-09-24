import functools
import datetime
import calendar
from voluptuous import Schema, Required, Optional, Invalid, Any, Coerce


DONGLE_LOG_SCHEMA = Schema({
    Required('imei'): int,
    Required('proto_num'): int,
    Required('pack'): dict,
    Required('frame'): bytes
})

RULE_SCHEMA = Schema({
    Required('unique_id'): int,  # configured_rule_id
    Required('code'): basestring,
    Required('extra'): dict
})


def LIST_OF_RULES_VALIDATOR():

    def validate(rules):
        if not isinstance(rules, list):
            raise Invalid("Rules must be of list type")
        for rule in rules:
            RULE_SCHEMA(rule)
        return rules

    return validate

LIST_OF_RULES_SCHEMA = Schema(LIST_OF_RULES_VALIDATOR())

SPEED_VIOLATION_EXTRA_SCHEMA = Schema({Required('v'): Coerce(int)}, extra=True)
RPM_VIOLATION_EXTRA_SCHEMA = Schema({Required('rpm'): Coerce(int)}, extra=True)
COLD_START_VIOLATION_EXTRA_SCHEMA = Schema({
    Required('t'): Coerce(int)}, extra=True)
ACC_VIOLATION_EXTRA_SCHEMA = Schema(
    {Required('acceleration'): float}, extra=True)
DECC_VIOLATION_EXTRA_SCHEMA = Schema(
    {Required('deceleration'): float}, extra=True)
MIL_VIOLATION_EXTRA_SCHEMA = Schema(
    {Required('MIL_status'): bool}, extra=True)
GEO_FENCE_VIOLATION_EXTRA_SCHEMA = Schema({
    Required('type'): basestring,
    Required('zone_idx'): int})
THROTTLE_POS_VIOLATION_EXTRA_SCHEMA = Schema({
    Required('throttle_pos'): Coerce(int)}, extra=True)
FUEL_CONSUMPTION_ABNORMAL_EXTRA_SCHEMA = Schema({
    Required('fuel_level_input'): Coerce(int),
    Required('prev_fuel_level_input'): Coerce(int),
    Required('actual_speed'): Coerce(float)}, extra=True)
REFUEL_EXTRA_SCHEMA = Schema({
    Required('fuel_level_input'): Coerce(int),
    Required('prev_fuel_level_input'): Coerce(int),
    Required('actual_speed'): Coerce(float)}, extra=True)
AVG_FUEL_CONSUMPTION_BOUNDS_EXTRA_SCHEMA = Schema({
    Required('fuel_consumption'): Coerce(int)}, extra=True)
RULE_VIOLATION_SCHEMA = Schema({
    Required('conf_rule_pk'): int,  # rule configured id
    Required('vehicle_pk'): Coerce(int),
    Required('rule_code'): basestring,
    Required('device_imei'): Coerce(int),
    Required('at'): int,
    Optional('where'): Any(list, tuple),
    Required('extra'): Any(
        SPEED_VIOLATION_EXTRA_SCHEMA,
        RPM_VIOLATION_EXTRA_SCHEMA,
        COLD_START_VIOLATION_EXTRA_SCHEMA,
        ACC_VIOLATION_EXTRA_SCHEMA,
        DECC_VIOLATION_EXTRA_SCHEMA,
        MIL_VIOLATION_EXTRA_SCHEMA,
        GEO_FENCE_VIOLATION_EXTRA_SCHEMA,
        THROTTLE_POS_VIOLATION_EXTRA_SCHEMA,
        FUEL_CONSUMPTION_ABNORMAL_EXTRA_SCHEMA,
        REFUEL_EXTRA_SCHEMA,
        AVG_FUEL_CONSUMPTION_BOUNDS_EXTRA_SCHEMA)
}, extra=True)


def LIST_OF_OBJ_VALIDATOR(obj_schema):

    def validate(objs):
        if not isinstance(objs, list):
            raise Invalid('Input arg must be of list type')
        for i, obj in enumerate(objs):
            objs[i] = obj_schema(obj)
        return objs

    return validate


def LIST_OF_VIOLATIONS_VALIDATOR():
    return LIST_OF_OBJ_VALIDATOR(RULE_VIOLATION_SCHEMA)

LIST_OF_VIOLATIONS = Schema(LIST_OF_VIOLATIONS_VALIDATOR())

VEHICLE_STAT_SCHEMA = Schema({})  # TODO. do it

VEHICLE_MIL_SCHEMA = Schema({
    Required('dtc'): list,
    Required('obd'): list,
}, extra=True)

VEHICLE_STATE = Schema({
    Required('vin'): basestring,
    Required('imei'): Any(basestring, bool),
    Required('pk'): int,
    Required('model'): basestring,
    Optional('stat'): VEHICLE_STAT_SCHEMA,
    Optional('is_online'): bool,
    Optional('MIL'): Any(bool, VEHICLE_MIL_SCHEMA)
}, extra=True)


def LIST_OF_VEHICLES_VALIDATOR():
    return LIST_OF_OBJ_VALIDATOR(VEHICLE_STATE)

SUBSCRIPTION_SCHEMA = Schema({
    Required('pk'): int,  # sql id
    Required('service_pk'): int,
    Required('service_name'): basestring,
    Required('connected_cars'): LIST_OF_VEHICLES_VALIDATOR(),
    Required('available_features'): list,
}, extra=True)


def LIST_OF_SUBSCRS_VALIDATOR():
    return LIST_OF_OBJ_VALIDATOR(SUBSCRIPTION_SCHEMA)

USER_SCHEMA = Schema({
    Required('pk'): int,
    Required('email'): basestring,
    Required('company_pk'): int,
    Required('subscriptions'): LIST_OF_SUBSCRS_VALIDATOR(),
}, extra=True)

NOTIFICATION_BODY_SCHEMA = Schema({
    Required('severity'): basestring,
    Required('code_name'): basestring,
    Required('actor'): dict,
    Required('dt'): basestring,
    Required('verb'): basestring,
    Required('subscription_id'): int,
    Optional('extra'): dict,
    Optional('action_object'): dict(),
    Optional('target'): dict(),
})

NOTIFICATION_SCHEMA = Schema({
    Required('body'): basestring,
    Required('recipient_list'): list
})


def WeakCoerce(type, msg=None):
    """Coerce a value to a type.

    If the type constructor throws a ValueError or TypeError, the value
    will be marked as Invalid.


    Default behavior:

        >>> validate = Schema(Coerce(int))
        >>> with raises(MultipleInvalid, 'expected int'):
        ...   validate(None)
        >>> with raises(MultipleInvalid, 'expected int'):
        ...   validate('foo')

    With custom message:

        >>> validate = Schema(Coerce(int, "moo"))
        >>> with raises(MultipleInvalid, 'moo'):
        ...   validate('foo')
    """
    @functools.wraps(WeakCoerce)
    def f(v):
        if not v:
            return None
        try:
            return type(v)
        except (ValueError, TypeError):
            raise Invalid(msg or ('expected %s' % type.__name__))
    return f


def coerce_qlink_time(strtime):
    try:
        return int(strtime)
    except:
        if isinstance(strtime, int):
            return strtime
        fmt = '%Y%m%d%H%M%S'
        return _ts(datetime.datetime.strptime(strtime, fmt))


def _ts(val):
    return calendar.timegm(val.utctimetuple())

COMMON_LOG_SCHEMA = Schema({
    Required('imei'): WeakCoerce(str),
    Required('device_tp'): WeakCoerce(str),
    Optional('vin'): WeakCoerce(str),
    Optional('external_power_voltage'): WeakCoerce(int),
    Optional('gps_accuracy'): WeakCoerce(int),
    Optional('speed'): Any(WeakCoerce(float), ''),
    Optional('heading'): WeakCoerce(int),
    Optional('altitude'): WeakCoerce(float),
    Optional('longitude'): WeakCoerce(float),
    Optional('latitude'): WeakCoerce(float),
    Optional('gps_utc_time'): int,
    Optional('mcc'): WeakCoerce(str),
    Optional('mnc'): WeakCoerce(str),
    Optional('lac'): WeakCoerce(str),
    Optional('cell_id'): WeakCoerce(str),
    Optional('mileage'): WeakCoerce(float),
    Optional('obd_connect_status'): WeakCoerce(bool),
    Optional('power_voltage'): WeakCoerce(int),
    Optional('supported_pids'): WeakCoerce(list),
    Optional('rpm'): WeakCoerce(int),
    Optional('engine_coolant_temp'): WeakCoerce(int),
    Optional('fuel_consumption'): WeakCoerce(float),
    Optional('DTCs_cleared_distance'): WeakCoerce(int),
    Optional('MIL_active_distance'): WeakCoerce(int),
    Optional('MIL_status'): WeakCoerce(bool),
    Optional('DTCs_number'): WeakCoerce(int),
    Optional('DTCs'): WeakCoerce(str),
    Optional('throttle_position'): WeakCoerce(int),
    Optional('engine_load'): WeakCoerce(int),
    Optional('fuel_level_input'): WeakCoerce(int),
    Optional('maf'): WeakCoerce(float),
    Optional('engine_torque'): WeakCoerce(int),
    Optional('total_fuel_consumption'): WeakCoerce(float),
    Optional('accelerator_pedal_position'): WeakCoerce(int),
    Optional('pto_active'): WeakCoerce(bool),
    Optional('turbo_pressure'): WeakCoerce(float),
    Optional('axle_weight_0'): WeakCoerce(float),
    Optional('axle_weight_1'): WeakCoerce(float),
    Optional('axle_weight_2'): WeakCoerce(float),
    Optional('axle_weight_3'): WeakCoerce(float),
    Optional('from_buffer'): WeakCoerce(bool)
}, extra=True)

TOW_STATE = 16
IGN_OFF_REST = 11
IGN_OFF_MOTION = 12
IGN_ON_REST = 21
IGN_ON_MOTION = 22
REST = 41
MOTION = 42

MOTION_STATES = ('tow', 'ignition_off')

CAR_MOTION_STATE = Schema({
    Required('imei'): WeakCoerce(int),
    Optional('gps_utc_time'): WeakCoerce(int),
    Optional('longitude'): WeakCoerce(float),
    Optional('latitude'): WeakCoerce(float),
    Optional('speed'): WeakCoerce(float),
    Required('state'): Any(TOW_STATE, IGN_OFF_REST, IGN_OFF_MOTION,
                           IGN_ON_REST, IGN_ON_MOTION, REST, MOTION)
})
