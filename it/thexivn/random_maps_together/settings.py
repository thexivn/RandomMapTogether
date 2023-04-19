from pyplanet.contrib.setting import Setting

MIN_PLAYER_LEVEL_SETTINGS = Setting(
    'it.thexivn.RMT.min_perm_start', 'min_perm_start',
    Setting.CAT_BEHAVIOUR, int,
    'permission level to start the RMT',
    default=2,
)
