import string


def remove_trailing_punctuation(word):
    while word[-1] in string.punctuation:
        word = word[:-1]
    return word


def remove_all_punctuation(msg):
    for char in string.punctuation:
        msg = msg.replace(char, '')
    return msg


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
