import json
import sys

from sgqlc.introspection import variables, query

from nflapi.nfl import NFL


def main():
    nfl = NFL(ua=('Mozilla/5.0 (X11; CrOS x86_64 10895.10.0) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/69.0.3497.21 Safari/537.36'))
    data = nfl.endpoint(query, variables())
    with open(sys.argv[1], 'w') as fp:
        json.dump(data, fp)


if __name__ == '__main__':
    main()
