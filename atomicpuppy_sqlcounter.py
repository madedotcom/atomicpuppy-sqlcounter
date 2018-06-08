import logging

from retrying import retry
from sqlalchemy import (
    Column,
    Integer,
    String,
    create_engine,
    MetaData,
    Table
)
from sqlalchemy.orm import mapper, scoped_session, sessionmaker
from sqlalchemy.orm.exc import UnmappedClassError
from sqlalchemy.orm.util import class_mapper

from atomicpuppy.atomicpuppy import EventCounter, counter_circuit_breaker

metadata = MetaData()

counters_table = Table(
    'atomicpuppy_counters', metadata,
    Column('key', String(4000), primary_key=True),
    Column('position', Integer),
)


class SqlCounter(EventCounter):

    class Counter:
        def __init__(self, key, position):
            self.key = key
            self.position = position

    _logger = logging.getLogger(__name__)

    def __init__(self, connection_string, instance):
        self._logger = logging.getLogger(__name__)
        self._engine = create_engine(connection_string)
        self._ensured_schema = False
        self._instance_name = instance
        self._setup_mapper()
        self._start_session = scoped_session(sessionmaker(bind=self._engine))

    @classmethod
    def _setup_mapper(cls):
        try:
            class_mapper(cls.Counter)
        except UnmappedClassError:
            mapper(cls.Counter, counters_table)

    @retry(wait_exponential_multiplier=1000, wait_exponential_max=1000, stop_max_delay=6000)
    def __getitem__(self, stream):
        self._logger.debug("Fetching last read event for stream " + stream)
        key = self._key(stream)
        val = self._read_position(key)
        if val is None:
            return -1

        val = int(val)
        self._logger.info(
            "Last read event for stream %s is %d",
            stream,
            val)
        return val

    @counter_circuit_breaker
    def __setitem__(self, stream, val):
        # insert or update where instance = xxx and stream = xxx
        key = self._key(stream)
        # make sure the schema is there
        self._ensure_schema()

        s = self._start_session()
        counter = s.query(self.Counter).filter_by(key=key).first()
        if counter:
            counter.position = val
        else:
            counter = self.Counter(key=key, position=val)
        s.add(counter)
        s.commit()
        s.close()


    def _read_position(self, key):
        # make sure the schema is there
        self._ensure_schema()
        s = self._start_session()
        counter = s.query(SqlCounter.Counter).filter_by(key=key).first()
        if counter:
            pos = counter.position
        else:
            pos = None
        s.close()
        return pos


    def _key(self, stream):
        return '{}:{}'.format(self._instance_name, stream)

    def _ensure_schema(self):
        if self._ensured_schema:
            return

        counters_table.create(self._engine, checkfirst=True)
        self._ensured_schema = True
