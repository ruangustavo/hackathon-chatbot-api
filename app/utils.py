from datetime import datetime


def str_to_date(datetime_str):
    format_str = "%Y-%m-%dT%H:%M:%S.%f%z"
    date = datetime.strptime(datetime_str, format_str)
    return date


def decode_to_utf8(string: str):
    return bytes(string, "utf-8").decode("unicode-escape")
