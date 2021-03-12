# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# GNU General Public License (GPL)
# ------------------------------------------------------------------------------

import time


def end_time(start_time, base_msg="Migration finished in ", return_seconds=False):
    """Display a end time message."""
    seconds = time.time() - start_time
    seconds = int(seconds)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    msg = base_msg
    if d:
        msg += "{0} day(s), {1} hour(s), " \
            "{2} minute(s), {3} second(s).".format(d, h, m, s)
    elif h:
        msg += "{0} hour(s), {1} minute(s), {2} second(s).".format(h, m, s)
    elif m:
        msg += "{0} minute(s), {1} second(s).".format(m, s)
    else:
        msg += "{0} second(s).".format(s)
    if return_seconds:
        return msg, seconds
    return msg
