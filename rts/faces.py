from multiprocessing import Process, Queue
from threading import Thread
import cv2
from scipy.io.idl import AttrDict
from blink import find_eyes, is_eyes, draw_eye, is_blink
import motion
from rts import RTS

delay = 0
ready = False
blink = ()


class Detector(object):
    def __init__(self, ready_callback, callback):
        self.ready_callback = ready_callback
        self.callback = callback
        self.queue = Queue()
        Process(target=self.start_detector, args=(self.queue,)).start()
        Thread(target=self.poll_detector, args=(self.queue,)).start()

    def start_detector(self, queue):
        # in separate process
        rts = RTS()

        def initialization(t, state):
            state.wnd_main = "Blink Detection"
            state.wnd_debug = "Diff VC"
            state.streaming = True
            state.debug = False
            state.init_stage = False
            state.tracking_stage = False
            state.usage_text = "'s' Start - 'r' Reset - 'q' Quit"
            state.locating_text = "Mode : Locating eye..."
            state.tracking_text = "Mode : Tracking eye..."
            state.blinked_text = "*Blinked*"
            state.prev = None
            state.diff = None
            state.tpl = ()
            state.comps = ()
            state.blink = ()
            state.color = (0, 255, 0)
            state.diff_color = (255, 255, 0)
            state.text_color = (0, 0, 255)
            state.font = cv2.FONT_HERSHEY_PLAIN
            state.delay = 0
            # Initialize VideoCapture
            state.vc, state.kernel = motion.init(state.wnd_main)

        def retrieve(t, state):
            state.key, state.frame = state.vc.read()
            cv2.putText(state.frame, state.usage_text, (20, 20), state.font, 1.0, state.text_color)

        def init_stage(t, state, queue):
            state.diff, state.contours = motion.get_components(state.frame, state.prev, state.kernel)
            state.comps = motion.get_moved_components(state.contours, 5, 5)
            if state.contours is not None and not state.tracking_stage:
                cv2.putText(state.frame, state.locating_text, (20, 220), state.font, 1.0, state.text_color)
                state.tracking_stage, state.tpl = is_eyes(state.comps, state.frame)
                if state.tracking_stage:
                    queue.put("READY")

        def tracking_stage(t, state, queue):
            cv2.putText(state.frame, state.tracking_text, (20, 220), state.font, 1.0, state.color)
            for eye in state.tpl:
                state.ROI = find_eyes(eye, state.frame)
                if len(state.ROI) == 4:
                    state.frame = draw_eye(state.ROI, state.frame, state.color)
                    state.diff = draw_eye(state.ROI, state.diff, state.diff_color)
                    if is_blink(state.comps, state.ROI):
                        state.blink = state.ROI
                        state.delay = 3
                        queue.put("BLINK")

        def post_process(t, state):
            # Save current frame for next process
            state.prev = state.frame

            # Write text if blinked
            if state.delay > 0 and state.tracking_stage:
                cv2.putText(state.frame, state.blinked_text, (state.blink[0], state.blink[1] - 2), state.font, 1.0,
                            state.text_color, 2)
                state.delay -= 1
            # Stream the regular frame for main window
            cv2.imshow(state.wnd_main, state.frame)
            # Stream the diff frame for debug window
            if state.diff is not None and state.debug:
                cv2.imshow(state.wnd_debug, state.diff)

            # Force to take the last 8 bits of the integer returned by waitKey
            key = cv2.waitKey(15)
            key = key & 255 if key + 1 else -1
            # [DEV : 'd' to Debug] 'q' to Quit, 'r' to Reset and 's' to Start
            if key == ord('q'):
                cv2.destroyAllWindows()
                state.vc.release()
                state.streaming = False
            elif key == ord('r') and state.init_stage:
                state.tracking_stage = False
            elif key == ord('d') and state.init_stage:
                state.debug = True
                cv2.namedWindow(state.wnd_debug)
            elif key == ord('s') and not state.init_stage:
                state.init_stage = True

        def calculate_stage(t, state, queue):
            if state.init_stage:
                init_stage(t, state, queue)
            if state.tracking_stage:
                tracking_stage(t, state, queue)
            post_process(t, state)
        # run flow
        state = AttrDict()
        def init_done(result):
            print("init done")
            rts.schedule(retrieve, (state,), retrieve_done)
        def retrieve_done(result):
            # print("retrieve done")
            rts.schedule(calculate_stage, (state, queue), None, 0.04, on_fail)
            rts.schedule(retrieve, (state,), retrieve_done, 0.15, None,
                         fail_policy="reschedule") # time_policy="constant")
        def on_fail(result):
            print("!! fail")
            # rts.schedule(retrieve, (state,), retrieve_done)
        rts.schedule(initialization, (state,), init_done)
        rts.queue.join()

    def poll_detector(self, queue):
        # same process. communicating detector
        while True:
            event = self.queue.get()
            if event == "READY":
                self.ready_callback()
            if event == "BLINK":
                self.callback()


if __name__ == '__main__':
    def ready():
        print("Blinked!")

    def callback():
        print("Blinked!")

    x = Detector(ready, callback)
