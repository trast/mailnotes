from subprocess import Popen, PIPE, STDOUT

def git_backtick(*args):
    return Popen(['git']+list(args), stdout=PIPE).communicate()[0]

def git_pipe(*args):
    p = Popen(['git']+list(args), stdout=PIPE)
    return p.stdout
