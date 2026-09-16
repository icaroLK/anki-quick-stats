from aqt import mw
from aqt.qt import QAction

__version__ = '1.5.0'

userOption = None


def getUserOption(key, default=None):
    global userOption
    if userOption is None:
        userOption = mw.addonManager.getConfig(__name__)
    if key in userOption:
        return userOption[key]
    userOption[key] = default
    writeConfig()
    return default


def setUserOption(key, value):
    global userOption
    if userOption is None:
        userOption = mw.addonManager.getConfig(__name__)
    userOption[key] = value
    writeConfig()


def writeConfig():
    mw.addonManager.writeConfig(__name__, userOption)


def _config_updated(_):
    global userOption
    userOption = None


mw.addonManager.setConfigUpdatedAction(__name__, _config_updated)

# imported after the config helpers above, since both modules need them at import time
from . import quick_stats_main_screen
from .settings_dialog import open_settings

_settings_action = QAction("📊 Quick Stats (Main Screen) Settings...", mw)
_settings_action.triggered.connect(open_settings)
mw.form.menuTools.addAction(_settings_action)
