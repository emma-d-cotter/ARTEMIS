from .comms_NIMS_sim import read_tracks
from .comms_pamguard import PAMGuard_read
from .comms_adcp import ADCP_read
from . import stage
from . import targets
import threading

class InstrumentComms:
    """
    Class to start all instrument communications and check their status.
    """
    def __init__(self, stage_instance):
        #TODO: Can make this check what streams are present, and start those
        # functions
        comms_functions = [read_tracks] #, PAMGuard_read, ADCP_read]
        self.threads = []
        for fun in comms_functions:
                self.threads.append(
                    threading.Thread(target=fun, args=(stage_instance,)))

    def start(self):
        """
        Start all communications fuctions.
        """
        for thread in self.threads:
            thread.start()

    def check_status(self):
        """
        Returns list of booleans indicating which functions are running
        """
        status = []
        for i, thread in enumerate(self.threads):
            status.append(thread.is_alive())

        return status
