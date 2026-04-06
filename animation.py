import threading
import time
import dearpygui.dearpygui as dpg

class AnimationState:
    def __init__(self):
        self.running = False

def animate_width(tag, target_width, anim_state, duration=0.25, steps=20):
    if not dpg.does_item_exist(tag) or anim_state.running:
        return
    
    start_width = dpg.get_item_width(tag)
    step_delay = duration / steps
    anim_state.running = True

    def run():
        for step in range(steps + 1):
            ease = 1 - (1 - (step / steps)) ** 3
            new_w = int(start_width + (target_width - start_width) * ease)
            if dpg.does_item_exist(tag):
                dpg.set_item_width(tag, max(0, new_w))
            time.sleep(step_delay)
        anim_state.running = False

    threading.Thread(target=run, daemon=True).start()