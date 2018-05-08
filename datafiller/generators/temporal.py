from __future__ import print_function, unicode_literals

from datetime import timedelta, datetime, date

from datafiller.generators.numeric import IntGenerator
from datafiller.scripts.cli import db

__author__ = "danishabdullah"
__all__ = ('IntervalGenerator', 'DateGenerator', 'TimestampGenerator')


# ??? This could also be based on FloatGenerator? '4.2 days' is okay for pg.
class IntervalGenerator(IntGenerator):
    """Generate intervals.

    - str unit: time unit for the interval, default is 's' (seconds)
    """
    DIRS = {'unit': str}

    def __init__(self, att, params=None):
        IntGenerator.__init__(self, att, params)
        self.unit = self.params.get('unit', 's')
        self.cleanParams(IntervalGenerator.DIRS)

    def genData(self):
        # ??? maybe it should not depend on db?
        return db.intervalValue(super(IntervalGenerator, self).genData(),
                                self.unit)


class DateGenerator(IntGenerator):
    """Generate dates between 'start' and 'end' at precision 'prec'.

    - Date ref: reference date
    - int dir: direction from reference date
    - int prec: precision in days
    """
    DIRS = {'start': str, 'end': str, 'prec': int}

    @staticmethod
    def parse(s):
        return datetime.date(datetime.strptime(s, "%Y-%m-%d"))

    def __init__(self, att, params=None):
        IntGenerator.__init__(self, att, params)
        self.offset = 0
        start, end = 'start' in self.params, 'end' in self.params
        ref = self.params['start'] if start else \
            self.params['end'] if end else \
                None
        if ref != None:
            self.ref = DateGenerator.parse(ref)
            self.dir = 2 * ('start' in self.params) - 1
        else:
            self.ref = date.today()
            self.dir = -1
        # precision, defaults to 1 day
        self.prec = self.params.get('prec', 1)
        assert self.prec > 0, \
            "{0}: 'prec' {1} not > 0".format(self, self.prec)
        # adjust size of both start & end are specified
        if start and end:
            dend = DateGenerator.parse(self.params['end'])
            assert self.ref <= dend, \
                "{0}: 'end' must be after 'start'".format(self)
            delta = (dend - self.ref) / self.prec
            self.setSize(delta.days + 1)
        self.cleanParams(DateGenerator.DIRS)

    def genData(self):
        d = self.ref + self.dir * \
            timedelta(days=self.prec * IntGenerator.genData(self))
        return db.dateValue(d)


class TimestampGenerator(IntGenerator):
    """Generate timestamps between 'start' and 'end'.

    - Timestamp ref: reference time
    - int dir: direction from reference time, -1 or 1
    - int prec: precision in seconds, default 60 seconds
    - str tz: set in this time zone, may be None
    """
    DIRS = {'tz': str}
    DIRS.update(DateGenerator.DIRS)

    @staticmethod
    def parse(s):
        return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")

    def __init__(self, att, params=None):
        IntGenerator.__init__(self, att, params)
        self.offset = 0
        self.tz = self.params.get('tz')
        start, end = 'start' in self.params, 'end' in self.params
        ref = self.params['start'] if start else \
            self.params['end'] if end else \
                None
        if ref != None:
            self.ref = TimestampGenerator.parse(ref)
            self.dir = 2 * ('start' in self.params) - 1
        else:
            self.ref = datetime.today()
            self.dir = -1
        # precision, defaults to 60 seconds
        self.prec = self.params.get('prec', 60)
        # set size
        if start and end:
            dend = TimestampGenerator.parse(self.params['end'])
            assert self.ref <= dend, \
                "{0}: 'end' must be after 'start'".format(self)
            d = (dend - self.ref) / self.prec
            # t = d.total_seconds() # requires 2.7
            t = (d.microseconds + (d.seconds + d.days * 86400) * 10 ** 6) / 10 ** 6
            self.setSize(int(t + 1))
        self.cleanParams(TimestampGenerator.DIRS)

    def genData(self):
        t = self.ref + self.dir * \
            timedelta(seconds=self.prec * \
                              super(TimestampGenerator, self).genData())
        # ??? should not depend on db
        return db.timestampValue(t, self.tz)
