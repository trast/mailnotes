#!/usr/bin/python

import sys
import os
import re
import cPickle as pickle # FIXME replace with DB
import time
import subprocess

from util import *

monthago = time.time() - 30*86400

def add_note(ref, sha, note):
    p = subprocess.Popen(['git', 'notes', '--ref='+ref, 'add', '-F-', sha],
                         stdin=subprocess.PIPE)
    p.communicate(note)

def write_notes(sha, tm, tz, author, subject):
    utctime = float(tm)
    key = (utctime, author, subject)
    if key not in mail:
        if utctime > monthago:
            print tz, key
        return
    print sha, mail[key]['message_id']
    add_note('refs/notes/message-id', sha, mail[key]['message_id'])

if __name__ == '__main__':
    try:
        boundary = []#open('commits.boundary').read().split()
    except IOError, e:
        boundary = []
    newheads = git_backtick('rev-parse', '--branches', '--remotes', '--tags').split()
    mail = pickle.load(open('mail.pickle', 'rb'))
    for line in git_pipe('rev-list', '--no-merges', '--format=%H %ad %an <%ae>\t%s', '--date=raw',
                         *(newheads+['--not']+boundary)):
        if line.startswith('commit '):
            continue
        line = line.rstrip('\n')
        sha, tm, tz, rest = line.split(' ', 3)
        author, subject = rest.split('\t', 1)
        write_notes(sha, tm, tz, author, subject)
    open('commits.boundary', 'w').write('\n'.join(newheads))
