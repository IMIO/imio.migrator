# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# GNU General Public License (GPL)
# ------------------------------------------------------------------------------

from plone import api

import time


def end_time(start_time,
             base_msg="Migration finished in ",
             return_seconds=False,
             total_number=None):
    """Display a end time message.
       If p_return_seconds=True, it will return the msg and the total seconds.
       If a integer is given to total_number, the msg is compeleted with
       number of elements processed per second."""
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

    if total_number is not None:
        # avoid divide by 0 if seconds = 0
        msg += " Updated %d elements, that is %d by second." % (
            total_number, total_number / (seconds or 1))

    if return_seconds:
        return msg, seconds
    return msg


def ensure_upgraded(package_name):
    """Make sure the given p_package_name is upgraded, this is useful when some
       code will rely on fact that a record is in the registry or so.
       profile_name must be like "collective.documentgenerator", we will turn
       it into a portal_setup compliant profile name."""
    from imio.migrator.migrator import Migrator
    migrator = Migrator(api.portal.get())
    migrator.upgradeProfile("profile-" + package_name + ":default")
