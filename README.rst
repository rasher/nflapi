NFL API
=======

The nflapi library provides an interface for the NFL api located at
https://api.nfl.com, documented at https://api.nfl.com/docs/.

Installing
==========

The library has not yet been released on PyPI, since it's still in a pretty
rough state. There's a distinct risk that this might not ever change. To
install, you can use pip's ability to to install directly from a git
repository::

  pip install -e git+git@github.com:rasher/nflapi.git#egg=nflapi

Examples
========

Basic boilerplate for getting going::

  >>> from nflapi import NFL
  >>> nfl = NFL(ua="nflapi example script")

That's it. You can now use the nfl object to query various objects off the NFL
api. A couple of helpers are added to perform common queries and return the
results as reasonable objects.

Getting the current season and week::

  >>> week = nfl.schedule.current_week()
  >>> print("{w.season} {w.seasonType} {w.week}".format(w=week))
  2018 PRE 2

Getting standings information::

  >>> teams, week = nfl.standings.current()
  >>> for team in teams:
  ...   print("{s.nickName} {s.overallWinPct}".format(t=team.standings[0])
  ...
  Steelers 0.5 ...

Have a look at [nflcli.py](nflapi/cli/nflcli.py) for more examples.

You can also query the API directly if you're feeling adventurous. Raw requests
(currently) return the parsed JSON response, rather than model classes::

  >>> response = nfl.request('/v1/achievements',
  ...                        s='{"$query":{"type":"SBMVP","season":2017}}',
  ...                        fs='{person{displayName}}')
  >>> print(response['data'][0]['person']['displayName'])
  Nick Foles

Damn straight.

A bit about the API
===================

The NFL api hosted on nfl.com is in an odd state. From its appearance, it would
appear that development on it has been halted before all planned features were
completed. As such, a lot of the examples simply do not work, or return only
incomplete data. The documentation notes this in some places, but not always.

The field selector (`fs` parameter) sometimes works, but mostly doesn't. Only
specific queries (`s` paramter) appear to be supported, though you can
sometimes get lucky that minor changes still work. In general, it's safest to
go by the queries listed on the endpoint pages in the documentation. The
queries on the example pages appear to be mostly fantasy.

Some documented endpoints simply do not exist. E.g. /venues.

The model also seems rather odd at times, for example returning standings as a
list.
