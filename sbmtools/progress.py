import sys
from time import sleep

class SimpleProgressBar:

    def __init__(self, maxval, width=10):
        self.maxval = maxval
        self.step = 1/(float(maxval)/100)
        self.width = width

    def update(self, val, progress=None):
        progress = int(round(val * self.step, 0))
        sys.stdout.write('\r[{0}] {1}%'.format('#' * (progress / self.width), progress))

    def finish(self):
        self.update(self.maxval)
        print

    def pause(self, time_):
        print
        print 'Pausing execution for %d s' % time_
        sleep(time_)