#!/usr/bin/python

import sys
import os
import re
import cPickle as pickle # FIXME replace with DB
import time
import subprocess
from collections import defaultdict

from util import *

monthago = time.time() - 30*86400

_eol_space_re = re.compile('[ \t]+$', re.MULTILINE)

class Notes(object):

    def __init__(self, refname, indexname):
        self._indexname = indexname
        self._env = { 'GIT_INDEX_FILE': indexname }
        self._env.update(os.environ)
        self._ref = refname
        self._reset()

    def _reset(self):
        self._cache = defaultdict(list)
        self._index = {}

    def extend(self, sha1, seq):
        for line in seq:
            self.append_line(sha1, line)

    def append_line(self, sha1, line):
        self._cache[sha1].append(line)

    def __contains__(self, sha1):
        return sha1 in self._cache

    def flush(self):
        try:
            os.unlink(self._indexname)
        except OSError:
            pass
        count = len(self._cache)
        gfi = subprocess.Popen(['git', 'fast-import', '--date-format=now'], stdin=subprocess.PIPE)
        w = gfi.stdin.write
        def write_data(data):
            w('data %d\n' % len(data))
            w(data)
            w('\n')
        w('commit %s\n' % self._ref)
        w('committer Thomas Rast <trast@inf.ethz.ch> now\n')
        write_data('Mass annotation by writenotes.py')
        w('from %s^0\n' % self._ref)
        w('deleteall\n')
        for cmt_sha1 in self._cache.iterkeys():
            count = count - 1
            sys.stdout.write('%6d\r' % count)
            sys.stdout.flush()
            notes = ''.join(self._cache[cmt_sha1]).strip('\n')
            notes = _eol_space_re.sub('', notes) + '\n'
            w('N inline %s\n' % cmt_sha1)
            write_data(notes)
        gfi.stdin.close()
        sys.stdout.write('\n')
        self._reset()


def write_notes(sha, tm, tz, author, subject):
    utctime = float(tm)
    key = (utctime, author, subject)
    if key not in mail:
        if utctime > monthago:
            print tz, key
        return
    m = mail[key]
    print sha, m['message_id']
    n_msgid.append_line(sha, mail[key]['message_id'])
    article = m['gmane_id']
    parent = m
    thread = article
    depth_limit = 100
    while 1:
        parent_irt = parent['in-reply-to']
        if parent_irt not in mail:
            break
        depth_limit -= 1
        if depth_limit < 0:
            break
        parent = mail[parent_irt]
        thread = parent['gmane_id']
        if parent['in-reply-to'] == parent:
            break
    if article is not None and thread is not None:
        n_gmane.append_line(sha, "http://thread.gmane.org/gmane.comp.version-control.git/%d/focus=%d" % (thread,article))

if __name__ == '__main__':
    try:
        boundary = []#open('commits.boundary').read().split()
    except IOError, e:
        boundary = []
    newheads = git_backtick('rev-parse', '--branches', '--remotes', '--tags').split()
    mail = pickle.load(open('mail.pickle', 'rb'))
    n_msgid = Notes('refs/notes/message-id', 'index.message-id')
    n_gmane = Notes('refs/notes/gmane', 'index.gmane')
    for line in git_pipe('rev-list', '--no-merges', '--format=%H %ad %an <%ae>\t%s', '--date=raw',
                         *(newheads+['--not']+boundary)):
        if line.startswith('commit '):
            continue
        line = line.rstrip('\n')
        sha, tm, tz, rest = line.split(' ', 3)
        author, subject = rest.split('\t', 1)
        write_notes(sha, tm, tz, author, subject)
    n_msgid.flush()
    n_gmane.flush()
    open('commits.boundary', 'w').write('\n'.join(newheads))
