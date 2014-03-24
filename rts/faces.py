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

#
# def loop(self, queue):
#     wnd_main = "Blink Detection"
#     wnd_debug = "Diff VC"
#     streaming = True
#     debug = False
#     init_stage = False
#     tracking_stage = False
#     usage_text = "'s' Start - 'r' Reset - 'q' Quit"
#     locating_text = "Mode : Locating eye..."
#     tracking_text = "Mode : Tracking eye..."
#     blinked_text = "*Blinked*"
#     prev = None
#     diff = None
#     tpl = ()
#     comps = ()
#     blink = ()
#     color = (0, 255, 0)
#     diff_color = (255, 255, 0)
#     text_color = (0, 0, 255)
#     font = cv2.FONT_HERSHEY_PLAIN
#     delay = 0
#     # Initialize VideoCapture
#     vc, kernel = motion.init(wnd_main)
#     while streaming:
#         # Register sequenced images and find all connected components
#         key, frame = vc.read()
#         # Write usage text
#         cv2.putText(frame, usage_text, (20, 20), font, 1.0, text_color)
#         if init_stage:
#             diff, contours = motion.get_components(frame, prev, kernel)
#             comps = motion.get_moved_components(contours, 5, 5)
#             # If not entering tracking_stage yet, try find eyes within contours
#             if not contours == None and not tracking_stage:
#                 cv2.putText(frame, locating_text, (20, 220), font, 1.0, text_color)
#                 tracking_stage, tpl = is_eyes(comps, frame)
#                 if tracking_stage:
#                     queue.put("READY")
#         # Get ROI from eye template against current frame
#         if tracking_stage:
#             cv2.putText(frame, tracking_text, (20, 220), font, 1.0, color)
#             for eye in tpl:
#                 ROI = find_eyes(eye, frame)
#                 if len(ROI) == 4:
#                     frame = draw_eye(ROI, frame, color)
#                     diff = draw_eye(ROI, diff, diff_color)
#                     if is_blink(comps, ROI):
#                         blink = ROI
#                         delay = 3
#                         queue.put("BLINK")
#         # Write text if blinked
#         if delay > 0 and tracking_stage:
#             cv2.putText(frame, blinked_text, (blink[0], blink[1] - 2), font, 1.0, text_color, 2)
#             delay -= 1
#         # Stream the regular frame for main window
#         cv2.imshow(wnd_main, frame)
#         # Stream the diff frame for debug window
#         if not diff == None and debug:
#             cv2.imshow(wnd_debug, diff)
#         # Save current frame for next process
#         prev = frame
#         # Force to take the last 8 bits of the integer returned by waitKey
#         key = cv2.waitKey(15)
#         key = key & 255 if key + 1 else -1
#         # [DEV : 'd' to Debug] 'q' to Quit, 'r' to Reset and 's' to Start
#         if key == ord('q'):
#             cv2.destroyAllWindows()
#             vc.release()
#             streaming = False
#         elif key == ord('r') and init_stage:
#             tracking_stage = False
#         elif key == ord('d') and init_stage:
#             debug = True
#             cv2.namedWindow(wnd_debug)
#         elif key == ord('s') and init_stage == False:
#             init_stage = True
#
#
# def calculation_done(self, result, queue):
#     is_blinked, is_ready, self.prev_frame, self.diff, self.comps, \
#     self.last_blink, self.tracking_stage, self.tpl = result
#     if is_ready:
#         queue.put("READY")
#     if is_blinked:
#         queue.put("BLINK")


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
            # Save current frame for next process
            state.prev = state.frame

        def tracking_stage(t, state, queue):
            print("tracking")
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
            # Save current frame for next process
            state.prev = state.frame

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
        # run flow
        state = AttrDict()
        def init_done(result):
            print("init done")
            rts.schedule(retrieve, (state,), retrieve_done)
        def retrieve_done(result):
            print("retrieve done")
            if state.init_stage:
                rts.schedule(init_stage, (state, queue), initstage_done, 0.1, on_fail)
            else:
                rts.schedule(post_process, (state,), iteration_done, 0.1, on_fail)
        def initstage_done(result):
            if state.tracking_stage:
                rts.schedule(tracking_stage, (state, queue), calculation_done, 0.1, on_fail)
            else:
                calculation_done(result)
        def calculation_done(result):
            print("calculation done")
            rts.schedule(post_process, (state,), iteration_done, 0.1, on_fail)
        def iteration_done(result):
            print("iteration done")
            rts.schedule(retrieve, (state,), retrieve_done)
        def on_fail(result):
            print("!! fail")
            rts.schedule(retrieve, (state,), retrieve_done)
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
