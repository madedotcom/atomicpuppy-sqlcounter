from .atomicpuppy_sqlcounter import SqlCounter


class WhenStoringANewSqlCounter:

    def given_an_in_memory_db_with_nothing(self):
        self.counter = SqlCounter(
            "sqlite://",
            "instance-name"
        )

    def because_a_counter_is_created_for_a_key(self):
        self.counter['test1-key'] = 42

    def it_should_store_the_new_counter(self):
        assert self.counter['test1-key'] == 42


class WhenUpdatingAnExistingSqlCounterPosition:

    def given_an_in_memory_db_with_a_counter_for_a_key(self):
        self.counter = SqlCounter(
            "sqlite://",
            "instance-name"
        )
        self.counter['test2-key1'] = 42
        self.counter['test2-key2'] = 2

    def because_a_counter_is_set_to_something_else(self):
        self.counter['test2-key1'] = 43
        self.counter['test2-key2'] = 3

    def it_should_update_the_position(self):
        assert self.counter['test2-key1'] == 43
        assert self.counter['test2-key2'] == 3


class WhenRetrievingANonExistingSqlCounter:

    def given_an_in_memory_db_with_nothing(self):
        self.counter = SqlCounter(
            "sqlite://",
            "instance-name"
        )

    def because_a_non_existing_key_is_retrieved(self):
        self.retrieved_position = self.counter['non-existing-key']

    def it_should_return_negative_one(self):
        assert self.retrieved_position == -1


class WhenTwoSqlCountersAreBuiltInTheSameThread:

    def given_two_sql_counters(self):
        self.counter1 = SqlCounter(
            "sqlite:///test.db",
            "instance-name"
        )
        self.counter2 = SqlCounter(
            "sqlite:///test.db",
            "instance-name"
        )

    def because_a_key_is_set_with_the_first(self):
        self.counter1['test4-key'] = 42

    def it_should_be_readable_by_the_second(self):
        assert self.counter2['test4-key'] == 42


