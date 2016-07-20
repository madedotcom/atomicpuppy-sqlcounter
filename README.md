What?
=============

This package provides a pluggable counter for AtomicPuppy based on SqlAlchemy.
It's been tested with PostgreSQL and Sqlite, but it should work with any other engine supported by SqlAlchemy.


How?
=============

This package requires AtomicPuppy and depends on SqlAlchemy.
You should install the package that SqlAlchemy requires to talk to your engine of choice.
For example, if you use PostgreSQL, you should also install `psycopg2`.

To use it, just pass the following configuration to AtomicPuppy:

```
counter:
    class: SqlCounter
    package: atomicpuppy_sqlcounter
    parameters:
        connection_string: <SQLALCHEMY CONNECTION STRING>
```
