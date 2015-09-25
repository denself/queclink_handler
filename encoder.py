# -*- coding: utf-8 -*-
from datetime import datetime, time
import json
import sqlalchemy as sa
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm.base import class_mapper
from sqlalchemy.orm.exc import DetachedInstanceError

__author__ = 'D.Ivanets'


class AlchemyEncoder(json.JSONEncoder):
    """
    This is a special object, that allows serialize SQLAlchemy object to JSON
    Usage: json.dumps(sqlAlchemy_object, cls=AlchemyEncoder)
    """
    def default(self, obj):
        """
        :param obj:
        :return: Dictionary of JSON serializable objects.
        :rtype: dict
        """
        if isinstance(obj.__class__, DeclarativeMeta):
            # An SQLAlchemy class
            fields = {}
            for field in [col.key for col in class_mapper(type(obj)).iterate_properties
                          if isinstance(col, sa.orm.ColumnProperty)]:
                try:
                    data = obj.__getattribute__(field)
                except DetachedInstanceError:
                    data = 'UNKNOWN'
                if field != 'dt_modify' and not field.startswith('_'):
                    try:
                        # this will fail on non-encodable values, like other classes
                        json.dumps(data)
                        fields[field] = data
                    except TypeError:
                        # Special handlers for unusual data types.
                        # Handler: datetime
                        if isinstance(data, datetime):
                            fields[field] = data.isoformat()
                        elif isinstance(data, time):
                            fields[field] = data.isoformat()
                        else:
                            fields[field] = None
            # a json-encodable dict
            return fields

        return json.JSONEncoder.default(self, obj)