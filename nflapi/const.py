API_HOST = 'https://api.nfl.com'

ENDPOINT_V1_REROUTE = '/v1/reroute'
ENDPOINT_IDENTITY_V3_TOKEN = '/identity/v3/token'
ENDPOINT_IDENTITY_V3_TOKEN_REFRESH = '/identity/v3/token/refresh'

ENDPOINT_FOOTBALL_V2 = '/football/v2'
FOOTBALL_GAME_BY_ID = ENDPOINT_FOOTBALL_V2 + "/games/{game_id}?withExternalIds={with_external_ids}"
FOOTBALL_GAMES_BY_WEEK = ENDPOINT_FOOTBALL_V2 + '/games/season/{season}/seasonType/{season_type}/week/{week}?withExternalIds={with_external_ids}'
FOOTBALL_WEEK_BY_DATE = ENDPOINT_FOOTBALL_V2 + '/weeks/date/{date:%Y-%m-%d}'
FOOTBALL_TEAMS_BY_SEASON = ENDPOINT_FOOTBALL_V2 + '/teams/history?season={season}&limit={limit}'
FOOTBALL_TEAM_BY_ID = ENDPOINT_FOOTBALL_V2 + '/teams/{id}'
FOOTBALL_STANDINGS_BY_WEEK = ENDPOINT_FOOTBALL_V2 + '/standings?seasonType={season_type}&week={week}&season={season}&limit={limit}'
FOOTBALL_COMBINE_PROFILES_BY_YEAR = ENDPOINT_FOOTBALL_V2 + '/combine/profiles?year={year}&combineAttendance={combine_attendance}&limit={limit}'
FOOTBALL_ROSTERS_BY_SEASON = ENDPOINT_FOOTBALL_V2 + '/rosters?season={season}&limit={limit}'
FOOTBALL_DRAFT_PICKS_REPORT_BY_YEAR = ENDPOINT_FOOTBALL_V2 + '/draft/picks/report?year={year}&limit={limit}'
FOOTBALL_STATS_LIVE_GAME_SUMMARIES_BY_WEEK = ENDPOINT_FOOTBALL_V2 + "/stats/live/game-summaries?season={season}&seasonType={season_type}&week={week}"

FOOTBALL_EXPERIENCE_WEEKLY_GAME_DETAILS = (ENDPOINT_FOOTBALL_V2 + '/experience/weekly-game-details?'
                                           'includeDriveChart={include_drive_chart}'
                                           '&includeReplays={include_replays}'
                                           '&includeStandings={include_standings}'
                                           '&includeTaggedVideos={include_tagged_videos}'
                                           '&season={season}'
                                           '&type={season_type}'
                                           '&week={week}')

ENDPOINT_EXPERIENCE_V1 = '/experience/v1'
EXPERIENCE1_DRAFT = ENDPOINT_EXPERIENCE_V1 + '/draft?year={year}&limit={limit}'
EXPERIENCE1_TEAMS = ENDPOINT_EXPERIENCE_V1 + '/teams?season={season}'

ENDPOINT_EXPERIENCE_V2 = '/experience/v2'
EXPERIENCE2_GAMEDETAILS_BY_ID = ENDPOINT_EXPERIENCE_V2 + ('/gamedetails/{id}'
                                          '?includeDriveChart={include_drive_chart}'
                                          '&includeReplays={include_replays}'
                                          '&includeStandings={include_standings}'
                                          '&includeTaggedVideos={include_tagged_videos}')

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
