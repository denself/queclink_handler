import datetime
import calendar


def now():
    return datetime.datetime.utcnow()


def _ts():
    now = datetime.datetime.now()
    return calendar.timegm(now.utctimetuple())


def ts2date(ts):
    return datetime.datetime.utcfromtimestamp(ts)


def dt2ts(dt):
    return calendar.timegm(dt.utctimetuple())


def to_dt(dt_str, pattern='%Y%m%d%H%M%S'):
    return datetime.datetime.strptime(dt_str, pattern)


def to_str(dt, pattern='%Y%m%d%H%M%S'):
    return datetime.datetime.strftime(dt, pattern)
