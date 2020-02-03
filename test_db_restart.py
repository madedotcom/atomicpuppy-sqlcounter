import pytest
import sqlalchemy
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
            if conn.explode == "execute":
                raise MockDisconnect("Lost the DB connection on execute")
            elif args and 'select relname from pg_class' in args[0]:
                cursor.description = [("relname", None, None, None, None, None)]
            elif args and 'SELECT atomicpuppy_counters.key' in args[0]:
                cursor.description = [("key", None, None, None, None, None), ("position", None, None, None, None, None)]
            elif args and "UPDATE atomicpuppy_counters" in args[0]:
                cursor.description = None
                fake_atomicpuppy_positions['key_1'] = args[1]["position"]
            else:
                return

        def close():
            cursor.fetchall = cursor.fetchone = Mock(
                side_effect=MockError("cursor closed")
            )

        def fetchall():
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


class WhenDatabaseRestartsSqlCounterPoolRecovers:
    """ When a db restarts the connections in the pool need to be refreshed. Sqlalchemy only discovers this the first time a connection
    is used and exception is raised.  Sqlalchemy recognises the raised exception as indicating a db restart and refreshes all the connections in its pool.
    Hence this first transaction post restart fails https://docs.sqlalchemy.org/en/13/core/pooling.html#pool-disconnects and it is up
    to the application to retry it. If, in addition, this first transaction is not closed then all subsequent transactions fail
    with sqlalchemy.exc.StatementError with message "Can't reconnect until invalid transaction is rolled back".
    This test shows that SqlCounter is behaving responsibly, closing sessions when exceptions are raised and hence is
    avoiding repeated "Can't reconnect until invalid transaction is rolled back" on db restart
    """

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


class WhenDatabaseRestartsBadlyBehavedSessionsCanMakePoolConnectionsUnusable:

    def _prepare_mock_dbapi(self):
        self.dbapi = MockDBAPI()
        self.db = testing_engine(
            "postgresql://foo:bar@localhost/test",
            options=dict(module=self.dbapi, _initialize=False),
        )
        self.db.dialect.is_disconnect = lambda e, conn, cursor: isinstance(
            e, MockDisconnect
        )
        self._start_session = scoped_session(sessionmaker(bind=self.db))

    def because_there_is_a_connection_in_the_pool_and_the_db_is_restarted(self):
        self._prepare_mock_dbapi()
        assert len(self.db.pool._pool.queue) == 0
        session = self._start_session()
        try:
            session.execute('SELECT atomicpuppy_counters.key FROM atomicpuppy_counters;')
        finally:
            session.close()
        assert len(self.db.pool._pool.queue) == 1

        self.dbapi.shutdown()
        self.dbapi.restart()

    def it_should_first_fail_as_disconnected_and_then_fail_again_with_transaction_needs_rollback(self):
        assert len(self.db.pool._pool.queue) == 1
        session = self._start_session()
        with pytest.raises(Exception) as ex:
            session.execute('SELECT atomicpuppy_counters.key FROM atomicpuppy_counters;')
        assert 'Lost the DB connection on execute' in str(ex.value)

        # Second attempt has the invalid transaction problem
        session = self._start_session()
        with pytest.raises(sqlalchemy.exc.StatementError) as ex:
            session.execute('SELECT atomicpuppy_counters.key FROM atomicpuppy_counters;')

        expected_error = "Can't reconnect until invalid transaction is rolled back"
        assert expected_error in str(ex.value)
        assert "SELECT atomicpuppy_counters.key FROM atomicpuppy_counters;" in str(ex.value)

    def cleanup_db(self):
        self.dbapi.dispose()
