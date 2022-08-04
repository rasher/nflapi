API_HOST = 'https://api.nfl.com'

ENDPOINT_V1_REROUTE = '/v1/reroute'

ENDPOINT_SHIELD_V3 = '/v3/shield'

ENDPOINT_FOOTBALL_V2 = '/football/v2'
FOOTBALL_GAME_BY_ID = "/games/{game_id}?withExternalIds={with_external_ids}"
FOOTBALL_GAMES_BY_WEEK = '/games/season/{season}/seasonType/{season_type}/week/{week}?withExternalIds={with_external_ids}'
FOOTBALL_WEEK_BY_DATE = '/weeks/date/{date:%Y-%m-%d}'
FOOTBALL_TEAMS_BY_SEASON = '/teams/history?season={season}&limit={limit}'
FOOTBALL_TEAM_BY_ID = '/teams/{id}'
FOOTBALL_STANDINGS_BY_WEEK = '/standings?seasonType={season_type}&week={week}&season={season}&limit={limit}'
FOOTBALL_COMBINE_BY_YEAR = '/combine/profiles?year={year}&combineAttendance={combine_attendance}&limit={limit}'
FOOTBALL_ROSTERS_BY_SEASON = '/rosters?season={season}&limit={limit}'
FOOTBALL_DRAFT_PICKS_REPORT_BY_YEAR = '/draft/picks/report?year={year}&limit={limit}'

CONFERENCE_NAMES = {
    'AFC': 'American Football Conference',
    'NFC': 'National Football Conference',
}

DIVISION_NAMES = {
    'AFC_EAST': 'AFC East',
    'AFC_NORTH': 'AFC North',
    'AFC_SOUTH': 'AFC South',
    'AFC_WEST': 'AFC West',
    'NFC_EAST': 'NFC East',
    'NFC_NORTH': 'NFC North',
    'NFC_SOUTH': 'NFC South',
    'NFC_WEST': 'NFC West',
}
