from django.test import TestCase
from django.utils import six, unittest
from .models import (
    TestModel,
    TestNullableModel,
    TestDefaultModel,
    DEFAULT_DURATION
)
from durationfield.utils import timestring
from datetime import timedelta
from durationfield.forms.widgets import DurationInput
from durationfield.utils.timestring import timedelta_to_string


class DurationFieldTests(TestCase):

    def setUp(self):
        self.test_tds = [
            timedelta(hours=1),  # No days, no micro, single-digit hour
            timedelta(hours=10),  # double-digit hour
            timedelta(hours=10, minutes=35),
            timedelta(days=1),  # Day, no micro
            timedelta(days=1, microseconds=0),  # Day, with micro
            timedelta(days=10),  # Days, no micro
            timedelta(days=10, microseconds=0),  # Days, with micro
        ]

        return super(DurationFieldTests, self).setUp()

    def _delta_to_microseconds(self, td):
        """
        Get the total number of microseconds in a timedelta, normalizing days and
        seconds to microseconds.
        """
        SECONDS_TO_US = 1000 * 1000
        MINUTES_TO_US = SECONDS_TO_US * 60
        HOURS_TO_US = MINUTES_TO_US * 60
        DAYS_TO_US = HOURS_TO_US * 24

        td_in_ms = td.days * DAYS_TO_US + td.seconds * SECONDS_TO_US + td.microseconds
        self.assertEqual(timedelta(microseconds=td_in_ms), td)

        return td_in_ms

    def testTimedeltaStrRoundtrip(self):
        for td in self.test_tds:
            td_str = timedelta_to_string(td) 
            td_from_str = timestring.str_to_timedelta(td_str)
            self.assertEqual(td_from_str, td)

    def testDbRoundTrip(self):
        """
        Data should remain the same when taking a round trip to and from the db
        """
        models = [TestModel, TestNullableModel, TestDefaultModel]

        for td in self.test_tds:
            for ModelClass in models:
                tm = ModelClass()
                tm.duration_field = td
                tm.save()

                tm_saved = ModelClass.objects.get(pk=tm.pk)
                self.assertEqual(tm_saved.duration_field, tm.duration_field)

    def testDefaultValue(self):
        """
        Default value should be empty and fetchable
        """
        model_test = TestNullableModel()
        model_test.save()
        model_test_saved = TestNullableModel.objects.get(pk=model_test.pk)

        self.assertEqual(model_test.duration_field, None)
        self.assertEqual(model_test_saved.duration_field, None)

    def testDefaultGiven(self):
        """
        Default value should use the default argument.
        """
        model_test = TestDefaultModel()
        model_test.save()

        model_test_saved = TestDefaultModel.objects.get(pk=model_test.pk)
        self.assertEqual(model_test.duration_field, DEFAULT_DURATION)
        self.assertEqual(model_test_saved.duration_field, DEFAULT_DURATION)

    def testApplicationType(self):
        """
        Timedeltas should be returned to the applciation
        """
        for td in self.test_tds:
            model_test = TestModel()
            model_test.duration_field = td
            model_test.save()
            model_test = TestModel.objects.get(pk=model_test.pk)
            self.assertEqual(td, model_test.duration_field)

            # Test with strings
            model_test = TestModel()
            model_test.duration_field =  timedelta_to_string(td) 
            model_test.save()
            model_test = TestModel.objects.get(pk=model_test.pk)
            self.assertEqual(td, model_test.duration_field)

            # Test with int
            model_test = TestModel()
            model_test.duration_field = self._delta_to_microseconds(td)
            model_test.save()
            model_test = TestModel.objects.get(pk=model_test.pk)
            self.assertEqual(td, model_test.duration_field)

    @unittest.skipIf(six.PY3, 'long not present in Python 3')
    def testLongInPython2(self):
        for td in self.test_tds:
            # Test with long
            model_test = TestModel()
            model_test.duration_field = long(self._delta_to_microseconds(td))
            model_test.save()
            model_test = TestModel.objects.get(pk=model_test.pk)
            self.assertEqual(td, model_test.duration_field)

    def testInputTime(self):
        delta = timestring.str_to_timedelta("10h 23m")
        seconds = (10 * 60 * 60) + (23 * 60)
        self.assertEqual(seconds, delta.seconds)

    def testInputTimeSeonds(self):
        delta = timestring.str_to_timedelta("12h 21m")
        seconds = (12 * 60 * 60) + (21 * 60)
        self.assertEqual(seconds, delta.seconds)

    def testInputTimeSecondsMicroseconds(self):
        delta = timestring.str_to_timedelta("11m")
        seconds = (11 * 60)
        self.assertEqual(seconds, delta.seconds)

    def testInputAll(self):
        delta = timestring.str_to_timedelta("1Y 10M 3w 2d 3m")
        days = (
            (1 * 365) +
            (10 * 30) +
            (3 * 7) +
            2
        )
        seconds = (
            (3 * 60)
        )
        self.assertEqual(
            days, delta.days
        )
        self.assertEqual(
            seconds, delta.seconds
        )

    def testInputAllAbbreviated(self):
        delta = timestring.str_to_timedelta("2Y 9M 1w 20d 0m")
        days = (
            (2 * 365) +
            (9 * 30) +
            (1 * 7) +
            20
        )
        seconds = (
            (0 * 60 * 60) 
        )
        self.assertEqual(
            days, delta.days
        )
        self.assertEqual(
            seconds, delta.seconds
        )

    def testInputDaysOnly(self):
        delta = timestring.str_to_timedelta("24 days")
        self.assertEqual(
            24, delta.days
        )
