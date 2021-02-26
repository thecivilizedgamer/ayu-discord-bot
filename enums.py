class Enum:

    @classmethod
    def options(cls):
        return list([getattr(Days, x) for x in dir(cls) if x.upper() == x])


class Emoji(Enum):
    CHECK_MARK = b'\xe2\x9c\x85'.decode()
    X_MARK = u'\u274C'
    PIN = u'\U0001F4CC'

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

    CLOCK = b'\xf0\x9f\x95\x92'.decode()

    A = b'\xf0\x9f\x87\xa6'.decode()
    B = b'\xf0\x9f\x87\xa7'.decode()
    C = b'\xf0\x9f\x87\xa8'.decode()
    D = b'\xf0\x9f\x87\xa9'.decode()
    E = b'\xf0\x9f\x87\xaa'.decode()
    F = b'\xf0\x9f\x87\xab'.decode()
    G = b'\xf0\x9f\x87\xac'.decode()
    H = b'\xf0\x9f\x87\xad'.decode()
    I = b'\xf0\x9f\x87\xae'.decode()
    J = b'\xf0\x9f\x87\xaf'.decode()
    K = b'\xf0\x9f\x87\xb0'.decode()
    L = b'\xf0\x9f\x87\xb1'.decode()
    M = b'\xf0\x9f\x87\xb2'.decode()
    N = b'\xf0\x9f\x87\xb3'.decode()
    O = b'\xf0\x9f\x87\xb4'.decode()
    P = b'\xf0\x9f\x87\xb5'.decode()
    Q = b'\xf0\x9f\x87\xb6'.decode()
    R = b'\xf0\x9f\x87\xb7'.decode()
    S = b'\xf0\x9f\x87\xb8'.decode()
    T = b'\xf0\x9f\x87\xb9'.decode()
    U = b'\xf0\x9f\x87\xba'.decode()
    V = b'\xf0\x9f\x87\xbb'.decode()
    W = b'\xf0\x9f\x87\xbc'.decode()
    X = b'\xf0\x9f\x87\xbd'.decode()
    Y = b'\xf0\x9f\x87\xbe'.decode()
    Z = b'\xf0\x9f\x87\xbf'.decode()


class Days(Enum):
    SUNDAY = "Sunday"
    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"
    SATURDAY = "Saturday"

    @staticmethod
    def ordered_days():
        return [Days.SUNDAY, Days.MONDAY, Days.TUESDAY, Days.WEDNESDAY, Days.THURSDAY, Days.FRIDAY, Days.SATURDAY]

    @staticmethod
    def str_to_int(day_str):
        return Days.ordered_days().index(day_str)

    @staticmethod
    def int_to_str(day_int):
        return Days.ordered_days()[day_int]


class CallbackResponse(Enum):
    STOP = 1
