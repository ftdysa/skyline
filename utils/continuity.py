import redis
import msgpack
import sys
import json
import socket
import time
from os.path import dirname, abspath
from multiprocessing import Process, Manager, log_to_stderr

# add the shared settings file to namespace
sys.path.insert(0, ''.join((dirname(dirname(abspath(__file__))), "/src" )))
import settings

metric = 'horizon.test.udp'

def check_continuity(metric, mini = False):
    r = redis.StrictRedis(unix_socket_path=settings.REDIS_SOCKET_PATH)
    if mini:
        raw_series = r.get(settings.MINI_NAMESPACE + metric)
    else:
        raw_series = r.get(settings.FULL_NAMESPACE + metric)

    if raw_series == None:
        print 'key not found at %s ' + metric
        return 0, 0, 0, 0, 0

    unpacker = msgpack.Unpacker()
    unpacker.feed(raw_series)
    timeseries = [ unpacked for unpacked in unpacker ]
    length = len(timeseries)

    start = time.ctime(int(timeseries[0][0]))
    end = time.ctime(int(timeseries[-1][0]))
    duration = (float(timeseries[-1][0]) - float(timeseries[0][0])) / 3600

    last = int(timeseries[0][0]) - 10
    total = 0
    bad = 0
    missing = 0
    for i, tuple in enumerate(timeseries):
        total += 1
        if int(tuple[0]) - last != 10:
            bad += 1
            missing += int(tuple[0]) - last
        last = tuple[0]
   
    timeseries.reverse()
    total_sum = sum([tuple[1] for i, tuple in enumerate(timeseries) if i < 50])

    return length, total_sum, start, end, duration, bad, missing

if __name__ == "__main__":
    length, total_sum, start, end, duration, bad, missing = check_continuity(metric)
    print ""
    print "Stats for full %s:" % metric
    print "Length of %s" % length
    print "Total sum of last 50 datapoints: %s" % total_sum
    print "Start time: %s" % start
    print "End time: %s" % end
    print "Duration: %.2f hours" % duration
    print "Number of missing data periods: %s" % bad
    print "Total duration of missing data in seconds: %s" % missing

    length, total_sum, start, end, duration, bad, missing = check_continuity(metric, True)
    print ""
    print "Stats for mini %s:" % metric
    print "Length: %s" % length
    print "Total sum of last 50 datapoints: %s" % total_sum
    print "Start time: %s" % start
    print "End time: %s" % end
    print "Duration: %.2f hours" % duration
    print "Number of missing data periods: %s" % bad
    print "Total duration of missing data in seconds: %s" % missing
