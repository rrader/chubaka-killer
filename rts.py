from Queue import PriorityQueue
from threading import Thread
import time

#python2 Gantt/gantt.py -c colors.cfg -t "RTS" -o v.gpl rts/gantt.dat
#gnuplot
#gnuplot> load "v.gpl"

class RTS(object):
    def __init__(self):
        self.queue = PriorityQueue()
        self.threads = []
        for i in range(1):
            t = Thread(target=self.worker)
            t.start()
            self.threads.append(t)
        self.processed_events = 0
        self.dropped_events = 0
        self.log = file("gantt.dat", "w")
        self.log2 = file("wait.dat", "w")
        self.log3 = file("work_time.dat", "w")
        self.log4 = file("processed_items.dat", "w")
        self.log5 = file("dropped_items.dat", "w")
        self.start = time.time()

    def worker(self):
        while True:
            item = self.queue.get()
            priority, time_sch, function, args, callback, deadline, fail_callback, fail_policy, time_policy = item
            time_q = time.time()
            thread = Thread(target=function, args=(time_q, ) + args)
            thread.start()
            # res = function(time_q, *args, **kwargs)
            thread.join(deadline)
            if thread.isAlive():
                # overtime
                thread._Thread__stop()
                print("KILLED")
                if fail_policy == "callback":
                    if fail_callback:
                        fail_callback(None)
                elif fail_policy == "reschedule":
                    print("rescheduled")
                    self.schedule(*item[1:])
                self.dropped_events += 1
                self.log.write("{name} {time_s} {time_e} fail\n".format(name=function.func_name,
                                                                        time_s=time_q - self.start,
                                                                        time_e=time.time() - self.start))
                self.log5.write("{name} {ctime} 1\n".format(name=function.func_name,
                                                             ctime=time.time() - self.start))
            else:
                time_end = time.time() - self.start
                self.log.write("{name} {time_s} {time_e} ok\n".format(name=function.func_name,
                                                                      time_s=time_q - self.start,
                                                                      time_e=time_end))
                if time_policy == "constant":
                    sleep_time = max((time_q + deadline) - time.time(), 0)
                    print("sleeping additionally %s for constant interval" % sleep_time)
                    time.sleep(sleep_time)
                    self.log.write("{name} {time_s} {time_e} placeholder\n".format(name=function.func_name,
                                                                                   time_s=time_end,
                                                                                   time_e=time_end + sleep_time))
                if callback:
                    callback(None)
                self.log3.write("{name} {ctime} {time}\n".format(name=function.func_name,
                                                             ctime=time.time() - self.start, time=time_end + self.start - time_q))
                self.log4.write("{name} {ctime} 1\n".format(name=function.func_name,
                                                             ctime=time.time() - self.start))
            self.log2.write("{name} {ctime} {time}\n".format(name=function.func_name,
                                                             ctime=time.time() - self.start, time=time_q - time_sch))
            self.log.flush()
            self.log2.flush()
            self.log3.flush()
            self.log4.flush()
            self.log5.flush()
            self.processed_events += 1
            self.queue.task_done()

            print("processed, dropped: ", self.processed_events, self.dropped_events)

    def schedule(self, function, args, callback=None, deadline=None,
                 fail_callback=None, fail_policy="callback", time_policy="free"):
        priority = time.time() + deadline if deadline else time.time() + 1000
        self.queue.put((priority, time.time(), function, args, callback, deadline, fail_callback, fail_policy, time_policy))
