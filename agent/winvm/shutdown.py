import win32security
import win32api
import sys
from ntsecuritycon import *


def AdjustPrivilege(priv, enable = 1):
    # Get the process token.
    flags = TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY
    htoken = win32security.OpenProcessToken(win32api.GetCurrentProcess(), flags)
    # Get the ID for the system shutdown privilege.
    id = win32security.LookupPrivilegeValue(None, priv)
    # Now obtain the privilege for this process.
    # Create a list of the privileges to be added.
    if enable:
        newPrivileges = [(id, SE_PRIVILEGE_ENABLED)]
    else:
        newPrivileges = [(id, 0)]
    # and make the adjustment.
    win32security.AdjustTokenPrivileges(htoken, 0, newPrivileges)


def go_shutdown(is_reboot=0):
    AdjustPrivilege(SE_SHUTDOWN_NAME)
    win32api.InitiateSystemShutdown(None, 'Shutdown msg from API Server', 10, 1, is_reboot)


if __name__ == '__main__':
    go_shutdown()
