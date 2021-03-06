import datetime
import string

from enums import Days


def remove_trailing_punctuation(word):
    while word[-1] in string.punctuation:
        word = word[:-1]
    return word


def remove_all_punctuation(msg):
    for char in string.punctuation:
        msg = msg.replace(char, '')
    return msg


def str_to_time(time_str, am_pm=None):
    if am_pm is None:
        time_str, am_pm = time_str.split(' ', maxsplit=1)
    am_pm = am_pm.strip().lower()

    if am_pm not in ['am', 'pm']:
        raise RuntimeError('Invalid AM/PM specifier')

    if ':' in time_str:
        hours, mins = time_str.split(':')
        hours = int(hours)
        mins = int(mins)
    else:
        hours = int(time_str)
        mins = 0
    if hours > 12 or hours < 1:
        raise RuntimeError('Invalid hour specified')
    if mins > 59 or mins < 0:
        raise RuntimeError('Invalid minutes specified')

    if am_pm == 'pm':
        hours += 12

    return hours, mins


def seconds_to_string(seconds):
    seconds = max(int(seconds), 0)

    weeks = seconds // 604800
    seconds -= 604800 * weeks

    days = seconds // 86400
    seconds -= 86400 * days

    hours = seconds // 3600
    seconds -= 3600 * hours

    minutes = seconds // 60
    seconds -= 60 * minutes

    msg = ''

    if weeks > 1:
        msg += f'{weeks} weeks '
    elif weeks == 1:
        msg += f'{weeks} week '
    if days > 1:
        msg += f'{days} days '
    elif days == 1:
        msg += f'{days} day '
    if hours > 1:
        msg += f'{hours} hours '
    elif hours == 1:
        msg += f'{hours} hour '
    if minutes > 1:
        msg += f'{minutes} minutes '
    elif minutes == 1:
        msg += f'{minutes} minute '
    if seconds > 1:
        msg += f'{seconds} seconds'
    elif seconds == 1:
        msg += f'{seconds} second'
    elif seconds == 0 and msg == '':
        msg = '0 seconds'

    return msg.strip()


def uncapitalize(msg):
    if len(msg) > 0:
        msg = msg[0].lower() + msg[1:]
    return msg


def capitalize(msg):
    if len(msg) > 0:
        msg = msg[0].upper() + msg[1:]
    return msg


def hours_and_minutes_to_str(hours, minutes):
    am_pm = 'AM'
    if hours > 12:
        hours -= 12
        am_pm = 'PM'

    time_str = str(hours) + ':'

    if minutes == 0:
        time_str += '00'
    elif minutes < 9:
        time_str += '0' + str(minutes)
    else:
        time_str += str(minutes)

    return time_str + f' {am_pm}'


def list_to_str(items):
    items = [str(x) for x in items]

    if len(items) == 1:
        return items[0]

    return ', '.join(items[:-1]) + f' and {items[-1]}'


def month_str_to_number(month_str):
    return {
        'jan': 1,
        'january': 1,
        'feb': 2,
        'february': 2,
        'mar': 3,
        'march': 3,
        'apr': 4,
        'april': 4,
        'may': 5,
        'jun': 6,
        'june': 6,
        'jul': 7,
        'july': 7,
        'aug': 8,
        'august': 8,
        'sep': 9,
        'september': 9,
        'oct': 10,
        'october': 10,
        'nov': 11,
        'november': 11,
        'dec': 12,
        'december': 12
    }[month_str.strip().lower()]


def get_alarm_description(alarm_name, days, times):
    description = f'{alarm_name} at '
    description += list_to_str([hours_and_minutes_to_str(x[0], x[1]) for x in times])
    description += ' on ' + list_to_str([Days.int_to_str(x) + 's' for x in days])
    return description


def get_local_time_from_offset(offset_mins):
    return datetime.datetime.utcnow() + datetime.timedelta(minutes=offset_mins)


def get_formatted_datetime(date=None):
    if date is None:
        date = datetime.datetime.utcnow()
    return date.strftime("%I:%M:%S %p on %b %m, %Y")
