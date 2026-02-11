import socket
import datetime


def is_internet_available():
    try:
        socket.create_connection(("8.8.8.8",53),timeout=3)
        return True
    except:
        return False


def natural_time():
    now = datetime.datetime.now()

    hour = now.strftime("%I").lstrip("0")
    minute = now.strftime("%M")

    if minute == "00":
        minute = "o clock"
    elif minute.startswith("0"):
        minute = "oh " + minute[1]

    period = "in the morning" if now.hour < 12 else \
             "in the afternoon" if now.hour < 18 else \
             "in the evening"

    return f"It is {hour} {minute} {period}"
