import math
import time

try:
    import weechat
except ImportError:
    print("This script must be run under WeeChat.")
    print("Get WeeChat now at: http://www.weechat.org/")


SCRIPT_NAME    = "hotstove"
SCRIPT_AUTHOR  = "SnoopJ"
SCRIPT_VERSION = "1.0"
SCRIPT_LICENSE = "MIT"
SCRIPT_DESC    = "Don't touch that hot stove (mute yourself instead!)"
SCRIPT_COMMAND = "hotstove"

DEFAULT_TIMEOUT = 5 * 60  # in seconds
SEC_TO_MSEC = 1000

weechat.register(SCRIPT_NAME, SCRIPT_AUTHOR, SCRIPT_VERSION, SCRIPT_LICENSE, SCRIPT_DESC, '', 'utf-8')
weechat.hook_command(
    SCRIPT_COMMAND,
    f"Shut up for [timeout] seconds (default: {DEFAULT_TIMEOUT} sec) in [channel] (default: channel of current buffer)",
    "[timeout] [channel]",
    "",
    "",
    "set_stfu_timeout",
    ""
)


SHUTUPS = {}


# NOTE: I'm pretty sure there's a mild bug here where setting multiple timeouts does
# not keep the first timer from firing, but it shouldn't really harm anything
def set_stfu_timeout(data, buffer, args):
    buf = weechat.current_buffer()
    try:
        args = args.split(maxsplit=2)
        if len(args) == 0:
            duration = DEFAULT_TIMEOUT
            dest = weechat.buffer_get_string(buf, "localvar_channel")
        elif len(args) == 1:
            duration, = args
            dest = weechat.buffer_get_string(buf, "localvar_channel")
        else:
            duration, dest, *rest = args

        duration = int(duration)
        weechat.prnt(buf, f"Shutting up in {dest=} for {duration} seconds")
        SHUTUPS[dest] = time.monotonic() + duration

        weechat.hook_timer(duration*SEC_TO_MSEC, 0, 1, "unset_stfu_timeout", dest)
    except Exception as exc:
        weechat.prnt(buf, f"Bad command, error was: {exc!r}")
        return weechat.WEECHAT_RC_ERROR

    return weechat.WEECHAT_RC_OK


def unset_stfu_timeout(dest, _):
    if dest in SHUTUPS:
        weechat.prnt(weechat.current_buffer(), f"Done shutting up for {dest=}")
        SHUTUPS.pop(dest)

    return weechat.WEECHAT_RC_OK


def stfu_filter(data, modifier, modifier_data, msg):
    cmd, dest, *rest = msg.split(maxsplit=2)

    timeout = SHUTUPS.get(dest, -1)
    now = time.monotonic()
    if timeout > now:
        weechat.prnt(weechat.current_buffer(), f"🔥HOT STOVE, DO NOT TOUCH!🔥 Remaining: [{math.ceil(timeout - now)} sec]")
        # send nothing at all
        return ""

    return msg


weechat.hook_modifier("irc_out1_privmsg", "stfu_filter", "")
