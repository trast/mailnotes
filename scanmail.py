#!/usr/bin/python

import sys
import os
import re
import cPickle as pickle # FIXME replace with DB
import email.Iterators
import email.Parser
import email.utils
import email.header


_msg_id_regex = re.compile(r'<([^<>]+)>')
def _parse_msg_id(str):
    m = _msg_id_regex.search(str)
    if m:
        return m.group(1)

def _detect_reply_id(msg):
    if msg['In-Reply-To']:
        return _parse_msg_id(msg['In-Reply-To'])
    if msg['References']:
        refs = ' '.join(msg.get_all('References'))
        ref_ids = [m.group(1) for m in _msg_id_regex.finditer(refs)]
        if ref_ids:
            return ref_ids[-1]

def _get_text_payloads(msg):
    if not msg.is_multipart():
        yield msg.get_payload()
        return
    for part in email.Iterators.typed_subpart_iterator(msg):
        if part.is_multipart():
            yield part.get_payload(0)
        else:
            yield part.get_payload()

def decode_quoted(s):
    try:
        ret = []
        for s, e in email.header.decode_header(s):
            if e:
                s = s.decode(e)
            ret.append(s)
        return ''.join(ret)
    except UnicodeError:
        return s

parser = email.Parser.Parser()

def decode_quoted(s):
    try:
        ret = []
        for s, e in email.header.decode_header(s):
            if e:
                s = s.decode(e)
            ret.append(s)
        return ''.join(ret)
    except UnicodeError:
        return s

_space_regex = re.compile(r'\s+')
def sanitize_single_line(s):
    if s is not None:
        return _space_regex.sub(' ', s)[:255]

_gmane_id_regex = re.compile(r'<http://permalink\.gmane\.org/gmane\.comp\.version-control\.git/(\d+)>')
def parse_mail(fname):
    msg = parser.parse(fname)
    gmane_id = None
    if msg['Archived-At']:
        m = _gmane_id_regex.match(msg['Archived-At'])
        if m:
            gmane_id = int(m.group(1))
    msgid = msg.get('Message-Id', None)
    if not msgid or not _parse_msg_id(msgid):
        if gmane_id:
            msgid = 'gmane-%d@mailnotes.thomasrast.ch' % gmane_id
        else:
            msgid = 'fallback-%X@mailnotes.thomasrast.ch' % random.randrange(2**32)
    else:
        msgid = _parse_msg_id(msgid)
    mail = {}
    mail['gmane_id'] = gmane_id
    mail['message_id'] = sanitize_single_line(msgid)
    if msg['From']:
        name, addr = email.utils.parseaddr(msg['From'])
        if name and addr:
            mail['from'] = sanitize_single_line("%s <%s>" % (decode_quoted(name), addr))
        else:
            mail['from'] = sanitize_single_line(decode_quoted(msg['From']))
    tm = None
    if msg['Date']:
        tm = email.utils.parsedate_tz(msg['Date'])
    if tm:
        tm = email.utils.mktime_tz(tm)
    else:
        tm = time.time()
    mail['date'] = tm
    mail['references'] = []
    if msg['References']:
        for m in _msg_id_regex.finditer(' '.join(msg.get_all('References'))):
            mail['references'].append(sanitize_single_line(m.group(1)))
    mail['in-reply-to'] = _detect_reply_id(msg)
    oldsubj = None
    subj = decode_quoted(msg['Subject'])
    mail['orig_subject'] = subj
    while oldsubj != subj:
        oldsubj = subj
        subj = subj.strip()
        if subj.startswith('Re:'):
            subj = subj[3:]
        if subj.startswith('re:'):
            subj = subj[3:]
        if subj.startswith(':'):
            subj = subj[1:]
        if subj.startswith('['):
            idx = subj.find(']')
            if idx > 0:
                subj = subj[idx+1:]
    mail['subject'] = subj
    data[msgid] = mail
    data[mail['date'], mail['from'], mail['subject']] = mail

if __name__ == '__main__':

    try:
        data = pickle.load(open('mail.pickle', 'rb'))
    except IOError, e:
        data = {}

    try:
        seen = pickle.load(open('mail-seen.pickle', 'rb'))
    except IOError, e:
        seen = set()

    for dirname in sys.argv[1:]:
        for fname in os.listdir(dirname):
            if fname in seen:
                continue
            parse_mail(open(os.path.join(dirname, fname)))
            seen.add(fname)

    pickle.dump(data, open('mail.pickle', 'wb'), -1)
    pickle.dump(seen, open('mail-seen.pickle', 'wb'), -1)
