from .atomicpuppy_sqlcounter import SqlCounter


class WhenStoringANewSqlCounter:

    def given_an_in_memory_db_with_nothing(self):
        self.counter = SqlCounter(
            "sqlite://",
            "instance-name"
        )

    def because_a_counter_is_created_for_a_key(self):
        self.counter['foo-key'] = 42

    def it_should_store_the_new_counter(self):
        assert self.counter['foo-key'] == 42


class WhenUpdatingAnExistingSqlCounterPosition:

    def given_an_in_memory_db_with_a_counter_for_a_key(self):
        self.counter = SqlCounter(
            "sqlite://",
            "instance-name"
        )
        self.counter['foo-key'] = 42
        self.counter['foo-key-2'] = 2

    def because_a_counter_is_set_to_something_else(self):
        self.counter['foo-key'] = 43
        self.counter['foo-key-2'] = 3

    def it_should_update_the_position(self):
        assert self.counter['foo-key'] == 43
        assert self.counter['foo-key-2'] == 3


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


