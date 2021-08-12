NFL API
=======

The nflapi library provides an interface for the NFL.com api. It essentially
acts like a browser, accessing the same functionality available through
nfl.com.

Installing
==========

The library has not yet been released on PyPI, since it's still in a pretty
rough state. There's a distinct risk that this might not ever change. To
install, you can use pip's ability to to install directly from a git
repository::

  pip install -e git+ssh://git@github.com:rasher/nflapi.git#egg=nflapi

Examples
========

Basic boilerplate to getting going::

  >>> from nflapi import NFL
  >>> nfl = NFL(ua="nflapi example script")

That's it. You can now use the nfl object to query various objects off the NFL
api. A couple of helpers are added to perform common queries and return the
results as reasonable objects.

Getting the current season and week::

  >>> week = nfl.schedule.current_week()
  >>> print(("{w.current_season[default]}"
             " {w.current_season_type[default]}"
             " {w.current_week[default]}").format(w=week))
  2018 PRE 2

Getting standings information::

  >>> records = nfl.standings.current()
  >>> for team, record in records:
  ...     print("{t.nick_name} {r.overall_pct:.3f}".format(t=team, r=record))
  ...
  Cardinals 0.500

Have a look at [nflcli.py](nflapi/cli/nflcli.py) for more examples.

You can also query the API directly if you're feeling adventurous.::

  >>> op = Operation(shield.Viewer)
  >>> player = op.viewer.player(id='3213464f-4c05-8566-2020-85b506da0baa')
  >>> player.person.display_name()
  >>> nfl.query(player).viewer.player.person.display_name
  'Nick Foles'

If you want to get even more wild, you can pass in a raw graphql query. In
that case you'll have to deal with the raw JSON response::

  >>> query = """{
  viewer{
    league{
      gamesByWeek(week_seasonValue: 2020,
                  week_seasonType: REG,
                  week_weekValue: 2) {
        id
        gameTime
        awayTeam{
          abbreviation
          }
          homeTeam{
            abbreviation
          }
        }
      }
    }
  }"""
  >>> games = nfl.endpoint(query)
  >>> games['data']['viewer']['league']['gamesByWeek'][0]['gameTime']
  '2020-09-22T00:15:00.000Z'

TODOs
=====

* Helpers for more object types
* A smarter approach to default field selections
* Documentation
* Tests, in a perfect world
