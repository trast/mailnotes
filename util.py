import os
from subprocess import Popen, PIPE, STDOUT, call

def git_backtick(*args):
    return Popen(['git']+list(args), stdout=PIPE).communicate()[0]

def git_pipe(*args):
    p = Popen(['git']+list(args), stdout=PIPE)
    return p.stdout

def git_communicate(*args, **kwargs):
    input = kwargs.pop('input', None)
    env = kwargs.pop('env', None)
    assert not kwargs
    p = Popen(['git']+list(args), stdin=PIPE, stdout=PIPE, env=env)
    out = p.communicate(input)[0]
    # ret = p.wait()
    # print "[%d] git %s" % (ret, ' '.join(args))
    return out

def git(*args):
    call(['git']+list(args))
