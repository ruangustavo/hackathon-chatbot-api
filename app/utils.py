def str_to_date(datetime_str):
    format_str = "%Y-%m-%dT%H:%M:%S.%f%z"
    datetime = datetime.strptime(datetime_str, format_str)
    return datetime


def decode_to_utf8(string: str):
    return bytes(string, "utf-8").decode("unicode-escape")
