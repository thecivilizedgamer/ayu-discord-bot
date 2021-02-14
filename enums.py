class Enum:

    @classmethod
    def options(cls):
        return list([getattr(Days, x) for x in dir(cls) if x.upper() == x])


class Emoji(Enum):
    CHECK = b'\xe2\x9c\x85'.decode()
    X = u'\u274C'
    ZERO = b'\xef\xb8\x8f\xe2\x83\xa3'.decode()
    ONE = b'1\xef\xb8\x8f\xe2\x83\xa3'.decode()
    TWO = b'2\xef\xb8\x8f\xe2\x83\xa3'.decode()
    THREE = b'3\xef\xb8\x8f\xe2\x83\xa3'.decode()
    FOUR = b'4\xef\xb8\x8f\xe2\x83\xa3'.decode()
    FIVE = b'5\xef\xb8\x8f\xe2\x83\xa3'.decode()
    SIX = b'6\xef\xb8\x8f\xe2\x83\xa3'.decode()
    SEVEN = b'7\xef\xb8\x8f\xe2\x83\xa3'.decode()
    EIGHT = b'8\xef\xb8\x8f\xe2\x83\xa3'.decode()
    NINE = b'9\xef\xb8\x8f\xe2\x83\xa3'.decode()


class Days(Enum):
    SUNDAY = "Sunday"
    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"
    SATURDAY = "Saturday"
