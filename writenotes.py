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
        input = []
        for cmt_sha1 in self._cache.iterkeys():
            count = count - 1
            sys.stdout.write('%6d\r' % count)
            sys.stdout.flush()
            notes = ''.join(self._cache[cmt_sha1]).strip('\n')
            notes = _eol_space_re.sub('', notes) + '\n'
            blob_sha1 = git_communicate('hash-object', '-w', '--stdin', input=notes).strip()
            input.append("100644 %s\t%s\n" % (blob_sha1, cmt_sha1))
        sys.stdout.write('\n')
        git_communicate('update-index', '--index-info', input=''.join(input), env=self._env)
        previous = git_backtick('rev-parse', self._ref).strip()
        if previous != self._ref:
            args = ['-p', previous]
            previous_arg = [previous]
        else:
            args = []
            previous_arg = []
        tree_sha1 = git_communicate('write-tree', env=self._env).strip()
        head_sha1 = git_communicate('commit-tree', tree_sha1, *args,
                                    **{'input':'Mass annotation by notes.py'}).strip()
        git('update-ref', '-m', 'Mass annotation by writenotes.py',
            self._ref, head_sha1, *previous_arg)
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

if __name__ == '__main__':
    try:
        boundary = []#open('commits.boundary').read().split()
    except IOError, e:
        boundary = []
    newheads = git_backtick('rev-parse', '--branches', '--remotes', '--tags').split()
    mail = pickle.load(open('mail.pickle', 'rb'))
    n_msgid = Notes('refs/notes/message-id', 'index.message-id')
    for line in git_pipe('rev-list', '--no-merges', '--format=%H %ad %an <%ae>\t%s', '--date=raw',
                         *(newheads+['--not']+boundary)):
        if line.startswith('commit '):
            continue
        line = line.rstrip('\n')
        sha, tm, tz, rest = line.split(' ', 3)
        author, subject = rest.split('\t', 1)
        write_notes(sha, tm, tz, author, subject)
    n_msgid.flush()
    open('commits.boundary', 'w').write('\n'.join(newheads))
