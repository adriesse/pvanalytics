"""Tests for :py:mod:`features.daytime`"""
import pytest
import pandas as pd
from pandas.testing import assert_series_equal
from pvlib.location import Location
from pvanalytics.features import daytime


@pytest.fixture(scope='module')
def albuquerque():
    return Location(35, -106, altitude=1500)


# Testing plan
#
# - [x] Can detect the daytime period in one day of data.
#
# - [x] Can detect the daytime period(s) in data where day spans two
#   dates.
#
# - [x] Can detect the correct daytime period in data where there is
#   1-2 hours of zeros mid-day
#
# - [x] Can detect daytime in a period where there are 'overcast' days
#   (i.e. ghi is 1/2 the normal value for a day or two)
#
# - [x] Can detect the daytime period in data with clipping (without
#   passing a "clipping mask")
#
# - [ ] Can detect daytime in a period where there are variable days.
#
# - [ ] Data with many missing values is handled gracefully
#
# - [x] Data with different timestamp spacing


def _assert_daytime_no_shoulder(clearsky, output):
    day = clearsky > 0
    shoulder = day & (clearsky <= 3)
    assert_series_equal(
        output | shoulder,
        day,
        check_names=False
    )


def test_daytime_diff(albuquerque):
    clearsky = albuquerque.get_clearsky(
        pd.date_range(start='1/1/2020', end='1/2/2020', freq='15T', tz='MST'),
        model='simplified_solis'
    )
    _assert_daytime_no_shoulder(
        clearsky['ghi'],
        daytime.diff(clearsky['ghi'])
    )


def test_midday_zero(albuquerque):
    clearsky = albuquerque.get_clearsky(
        pd.date_range(start='1/1/2020', end='1/20/2020', freq='15T', tz='MST'),
        model='simplified_solis'
    )
    ghi = clearsky['ghi']
    day = ghi > 0
    shoulder_time = day & (ghi <= 2)
    ghi.loc[ghi['1/3/2020'].between_time('12:00', '14:00').index] = 0
    assert_series_equal(
        daytime.diff(ghi) | shoulder_time,
        day,
        check_names=False
    )


def test_daytime_with_clipping(albuquerque):
    clearsky = albuquerque.get_clearsky(
        pd.date_range(start='1/1/2020', end='1/10/2020', freq='15T', tz='MST'),
        model='simplified_solis'
    )
    ghi = clearsky['ghi'].copy()
    ghi.loc[ghi >= 500] = 500
    _assert_daytime_no_shoulder(
        clearsky['ghi'],
        daytime.diff(ghi)
    )
    # Include a period where data goes to zero during clipping and
    # returns to normal after the clipping is done
    ghi.loc[ghi['1/3/2020'].between_time('12:30', '15:30').index] = 0
    _assert_daytime_no_shoulder(
        clearsky['ghi'],
        daytime.diff(ghi)
    )


def test_daytime_overcast(albuquerque):
    clearsky = albuquerque.get_clearsky(
        pd.date_range(start='1/1/2020', end='1/10/2020', freq='15T', tz='MST'),
        model='simplified_solis'
    )
    ghi = clearsky['ghi']
    ghi.loc['1/3/2020':'1/5/2020'] *= 0.5
    ghi.loc['1/7/2020':'1/8/2020'] *= 0.6
    _assert_daytime_no_shoulder(
        ghi,
        daytime.diff(ghi)
    )


def test_daytime_split_day():
    location = Location(35, -150)
    clearsky = location.get_clearsky(
        pd.date_range(start='1/1/2020', end='1/10/2020', freq='15T'),  # no tz
        model='simplified_solis'
    )
    _assert_daytime_no_shoulder(
        clearsky['ghi'],
        daytime.diff(clearsky['ghi'])
    )


def test_daytime_hour_spacing(albuquerque):
    clearsky = albuquerque.get_clearsky(
        pd.date_range(start='1/1/2020', end='1/20/2020', freq='H'),
        model='simplified_solis'
    )
    _assert_daytime_no_shoulder(
        clearsky['ghi'],
        daytime.diff(clearsky['ghi'])
    )
    # punch a mid-day hole
    ghi = clearsky['ghi'].copy()
    ghi.loc['1/10/2020 12:00':'1/10/2020 14:00'] = 0
    _assert_daytime_no_shoulder(
        clearsky['ghi'],
        daytime.diff(ghi)
    )


def test_daytime_minute_spacing(albuquerque):
    clearsky = albuquerque.get_clearsky(
        pd.date_range(start='1/1/2020', end='1/20/2020', freq='T'),
        model='simplified_solis'
    )
    _assert_daytime_no_shoulder(
        clearsky['ghi'],
        daytime.diff(clearsky['ghi'])
    )
    # punch a mid-day hole
    ghi = clearsky['ghi'].copy()
    ghi.loc['1/10/2020 12:00':'1/10/2020 14:00'] = 0
    _assert_daytime_no_shoulder(
        clearsky['ghi'],
        daytime.diff(ghi)
    )

def test_daytime_daylight_savings(albuquerque):
    spring = pd.date_range(
        start='2/10/2020',
        end='4/10/2020',
        freq='15T',
        tz='America/Denver'
    )
    clearsky_spring = albuquerque.get_clearsky(
        spring,
        model='simplified_solis'
    )
    _assert_daytime_no_shoulder(
        clearsky_spring['ghi'],
        daytime.diff(clearsky_spring['ghi'])
    )
    fall = pd.date_range(
        start='10/1/2020',
        end='12/1/2020',
        freq='15T',
        tz='America/Denver'
    )
    clearsky_fall = albuquerque.get_clearsky(
        fall,
        model='simplified_solis'
    )
    _assert_daytime_no_shoulder(
        clearsky_fall['ghi'],
        daytime.diff(clearsky_fall['ghi'])
    )
