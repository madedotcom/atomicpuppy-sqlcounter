import pytest
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.testing.engines import testing_engine
from sqlalchemy.testing.mock import Mock

from .atomicpuppy_sqlcounter import SqlCounter


class MockError(Exception):
    pass


class MockDisconnect(MockError):
    pass


def mock_connection():
    fake_atomicpuppy_positions = {'key_1': None}

    def mock_cursor():

        def execute(*args, **kwargs):
            print(f' in execute with args {args}')
            if conn.explode == "execute":
                raise MockDisconnect("Lost the DB connection on execute")
            elif args and 'select relname from pg_class' in args[0]:
                cursor.description = [("relname", None, None, None, None, None)]
            elif args and 'SELECT atomicpuppy_counters.key' in args[0]:
                print(f' execute args for select from atomicpuppy_counters.key')
                cursor.description = [("key", None, None, None, None, None), ("position", None, None, None, None, None)]
            elif args and "UPDATE atomicpuppy_counters" in args[0]:
                print(f' updating what are the args {args}')
                print(f' value to update to {args[1]["position"]} current value is {fake_atomicpuppy_positions["key_1"]}')
                cursor.description = None
                print(f' about to updated counter value to {args[1]["position"]}')
                fake_atomicpuppy_positions['key_1'] = args[1]["position"]
                print(f'updated counter value is {fake_atomicpuppy_positions["key_1"]}')
            else:
                return

        def close():
            cursor.fetchall = cursor.fetchone = Mock(
                side_effect=MockError("cursor closed")
            )

        def fetchall():
            print(f' in fetchall with cursor {cursor} and type {type(cursor)} and description {cursor.description} ')
            print(f' in fetchall with current counter_value {fake_atomicpuppy_positions["key_1"]}')
            return [['key_1', fake_atomicpuppy_positions["key_1"]]]

        def fetchone():
            print(f' in fetchone with cursor {cursor} and type {type(cursor)} and description {cursor.description}')
            return [['atomicpuppy_counters']]

        cursor = Mock(
            execute=Mock(side_effect=execute), close=Mock(side_effect=close), fetchall=Mock(side_effect=fetchall),
            fetchone=Mock(side_effect=fetchone)
        )
        cursor.rowcount = 1
        return cursor

    def cursor():
        while True:
            yield mock_cursor()

    def rollback():
        return

    conn = Mock(
        rollback=Mock(side_effect=rollback), cursor=Mock(side_effect=cursor())
    )
    return conn


def MockDBAPI():
    connections = []
    stopped = [False]

    def connect():
        while True:
            if stopped[0]:
                raise MockDisconnect("database is stopped")
            conn = mock_connection()
            connections.append(conn)
            yield conn

    def shutdown(explode="execute", stop=False):
        stopped[0] = stop
        for c in connections:
            c.explode = explode

    def restart():
        stopped[0] = False
        connections[:] = []

    def dispose():
        stopped[0] = False
        for c in connections:
            c.explode = None
        connections[:] = []

    return Mock(
        connect=Mock(side_effect=connect()),
        shutdown=Mock(side_effect=shutdown),
        dispose=Mock(side_effect=dispose),
        restart=Mock(side_effect=restart),
        paramstyle="named",
        connections=connections,
        Error=MockError,
    )


class WhenDatabaseRestartsCounterRecovers:

    def _prepare_mock_dbapi(self):
        self.dbapi = MockDBAPI()
        self.db = testing_engine(
            "postgresql://foo:bar@localhost/test",
            options=dict(module=self.dbapi, _initialize=False),
        )
        self.db.dialect.is_disconnect = lambda e, conn, cursor: isinstance(
            e, MockDisconnect
        )

    def given_an_sql_counter(self):
        self._prepare_mock_dbapi()
        self.counter = SqlCounter("postgresql://foo:bar@localhost/test", "instance-name")
        self.counter._engine = self.db
        self.counter._start_session = scoped_session(sessionmaker(bind=self.db))

    def because_there_is_a_connection_in_the_pool_and_the_db_is_restarted(self):
        assert len(self.counter._engine.pool._pool.queue) == 0
        self.counter['key_1'] = 20
        print(f' reading the value back that we just set to 20')
        val = self.counter['key_1']
        assert val == 20
        assert len(self.counter._engine.pool._pool.queue) == 1

        self.dbapi.shutdown()
        self.dbapi.restart()

    def it_should_first_fail_as_disconnected_and_then_recover(self):
        assert len(self.counter._engine.pool._pool.queue) == 1
        with pytest.raises(Exception) as ex:
            self.counter['key_1'] = 2
        assert 'Lost the DB connection on execute' in str(ex.value)

        assert len(self.counter._engine.pool._pool.queue) == 1
        self.counter['key_1'] = 3
        val = self.counter['key_1']
        assert val == 3

    def cleanup_db(self):
        self.dbapi.dispose()
