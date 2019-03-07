from __future__ import annotations
from typing import List, Optional, Set, Union, Tuple
import re


available_time_regex = re.compile(r'''
    (?P<start_time>\d+(?:[:]{0,1}\d+)?)     # start_time i.e. 7, 7:30, 7-30 or 730 or 75 (clearly invalid)
    \s*                                     # Potential space seperator between start_time and 12-hour clock indicator
    (?P<SI>am|a\.m|a\.m\.|pm|p\.m|p\.m\.)?  # Potential SI (start indicator) can be used for 12-hour clock format
    (?:[-: ]                                # Potential start_time and end_time seperator [-: ]
    (?P<end_time>\d+(?:[:]{0,1}\d+)?)       # Potential end_time (same as start_time)
    \s*                                     # Potential space seperator between end_time and 12-hour clock indicator
    (?P<EI>am|a\.m|a\.m\.|pm|p\.m|p\.m\.))? # Potential EI (end indicator) can be used for 12-hours clock format
''', re.I | re.M | re.VERBOSE)

twelve_hour_format_regex = re.compile(r'am|a\.m|a\.m\.|pm|p\.m|p\.m\.', re.I)
am_format_regex = re.compile(r'am|a\.m|a\.m\.', re.I)
pm_format_regex = re.compile(r'pm|p\.m|p\.m\.', re.I)

class Time():
    def __init__(self, hours: int, minutes: int):
        self.hours = hours
        self.minutes = minutes

    def __str__(self):
        return '{}:{}'.format(str(self.hours).rjust(2, '0'), str(self.minutes).ljust(2, '0'))

class TimeSlot():
    def __init__(self, start_time: Time, end_time: Optional[Time] = None):
        self.start_time = start_time
        self.end_time = end_time

    def __hash__(self):
        return hash((self.start_time, self.end_time))

    def __eq__(self, other: TimeSlot):
        return self.start_time == other.start_time and\
               self.end_time == other.end_time    
    
    def __str__(self):
        return '[{}, {}]'.format(self.start_time, self.end_time if self.end_time else '')

def get_24_hour_format(hour: Union[int, str], indicator: str):
    """
    Returns the hour represented by 24 hour format
    """
    hour = int(hour)
    # If it is hour 12 and AM then the 24 hour format becomes 0
    if hour == 12 and am_format_regex.match(indicator):
        hour = 0
    elif pm_format_regex.match(indicator):
        hour = hour + 12
    
    return hour % 24

def convert_to_time_slot(available_time: str):
    """
    Helper function to convert a given available time to a useful TimeSlot object.
    Examples of available_time:
        7:30 pm-9pm, 10pm-12am
5am
5
7pm-9pm
10A.M
    """

def parse_potential_time_slot(available_time: str) -> Optional[Tuple[str]]:
    """
    Helper function to convert a given available time to a tuple
    Examples of available_time:
        7:30 pm-9pm would return ('7:30', 'pm', '9', 'pm')
        10pm-12am   would return ('10', 'pm', '12', 'am')
        5am         would return ('5', 'am', '', '')  
        5           would return ('5', '', '', '')     
        7-9pm       would return ('7', '', '9', 'pm')  
        10pm-12     would return ('10', 'pm', '12', '')
"""
    match = available_time_regex(available_time)
    if match:
        start_time = match.group('start_time')
        end_time = match.group('end_time')
        start_indicator = match.group('SI') or ''
        end_indicator = match.group('EI')  or ''

        return (start_time, start_indicator, end_time, end_indicator)
    else:
        return None

def get_hours_minutes(time: str) -> Tuple[int, int]:
    minutes = 0
    if ':' in time:
            hours, minutes = [int(val) for val in time.split(':')]
    else:
        hours = int(time)
    return hours, minutes

def get_available_times_from_line(line: str):
    time_slots: Set[TimeSlot] = set()
    temp = []
    
    # For every match of the available_time_regex we have
    for match in available_time_regex.finditer(line):
        uses_24_hour_format = True
        if match:
            start_time = match.group('start_time')
            end_time = match.group('end_time')
            start_indicator = match.group('SI') or ''
            end_indicator = match.group('EI')  or ''

            # Check to see if it uses 12 hour format
            if twelve_hour_format_regex.match(start_indicator) or\
               twelve_hour_format_regex.match(end_indicator):
                uses_24_hour_format = False

            temp.append((start_time, start_indicator, end_time, end_indicator, uses_24_hour_format))

    for temp_slot in temp:
        print('---',temp_slot)
        # Grab start_time
        start_hour, start_minute = get_hours_minutes(temp_slot[0])

        # Adjust to 24 hours if needed
        if not temp_slot[-1]:
            start_hour = get_24_hour_format(start_hour, temp_slot[1])

        # Grab end_time
        end_time = None
        if temp_slot[2]:
            end_hour, end_minute = get_hours_minutes(temp_slot[2])
            # Adjust to 24 hours if needed
            if not temp_slot[-1]:
                # Both given
                if temp_slot[1] and temp_slot[3]:
                    end_hour = get_24_hour_format(end_hour, temp_slot[1])
                # SI given, EI not
                if temp_slot[1] and not temp_slot[3]:
                    end_hour = get_24_hour_format(end_hour, temp_slot[1])
                # SI blank, EI given
                elif not temp_slot[1] and temp_slot[3]:
                    start_hour = get_24_hour_format(start_hour, temp_slot[3])
                # Neither give
                elif not temp_slot[1] and not temp_slot[3]:
                    # Assume we start in p.m.
                    start_hour = get_24_hour_format(start_hour, 'pm')
                    # If end is earlier than start or is 12, we assume morning, i.e. late into the night
                    if end_hour < start_hour or end_hour == 12:
                        end_hour = get_24_hour_format(end_hour, 'am')
                    # Otherwise afternoon
                    else:
                        end_hour = get_24_hour_format(end_hour, 'pm')
            end_time = Time(end_hour, end_minute)
        else:
            if not temp_slot[1]:
                start_hour = get_24_hour_format(start_hour, 'pm')
        start_time = Time(start_hour, start_minute)
        print(start_hour)
        print(start_time)
        print(end_time)


            
        
        time_slots.add(TimeSlot(start_time, end_time))
    
    return time_slots
            

if __name__ == '__main__':
    input_str = '''
7:30 pm-9pm, 10pm-12am
5am
5
7pm-9pm
10A.M'''
    time_slots = get_available_times_from_line(input_str)
    for time_slot in time_slots:
        print(time_slot)