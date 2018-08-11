#!/usr/bin/env python

from nflapi import NFL
import logging

def main():
    logging.basicConfig(level=logging.DEBUG)
    nfl = NFL(ua='Mozilla/5.0 (X11; CrOS x86_64 10895.10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.21 Safari/537.36')
    cw = nfl.schedule.current_week()
    print("{w.season} {w.seasonType} {w.week}".format(w=cw))
