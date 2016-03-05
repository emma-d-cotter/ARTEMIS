from .comms_NIMS_sim import read_tracks
from .comms_pamguard import PAMGuard_read
from .comms_adcp import ADCP_read
from . import stage
from . import targets
import threading

class InstrumentComms:

    def __init__(self, stage_instance):

        comms_functions = [read_tracks, PAMGuard_read, ADCP_read]
        self.threads = []
        for fun in comms_functions:
                self.threads.append(
                    threading.Thread(target=fun, args=(stage_instance,)))

    def start(self):
        for thread in self.threads:
            thread.start()

    def check_status(self):
        
        status = []
        for i, thread in enumerate(self.threads):
            status.append(thread.is_alive())

        return status
