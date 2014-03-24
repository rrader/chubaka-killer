from Queue import Queue
from threading import Thread
import time


class RTS(object):
    def __init__(self):
        self.queue = Queue()
        self.thread = Thread(target=self.worker)
        self.thread.start()
        self.processed_events = 0
        self.dropped_events = 0

    def worker(self):
        while True:
            item = self.queue.get()
            time_q, function, args, callback, deadline, fail_callback = item
            thread = Thread(target=function, args=(time_q, ) + args)
            thread.start()
            # res = function(time_q, *args, **kwargs)
            thread.join(deadline)
            if thread.isAlive():
                # overtime
                thread._Thread__stop()
                print("KILLED")
                if fail_callback:
                    fail_callback(None)
                self.dropped_events += 1
            else:
                if callback:
                    callback(None)
            self.processed_events += 1
            self.queue.task_done()

    def schedule(self, function, args, callback=None, deadline=None, fail_callback=None):
        self.queue.put((time.time(), function, args, callback, deadline, fail_callback))
