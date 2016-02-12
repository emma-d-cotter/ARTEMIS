# TO ADD:
# - calculate actual velocity
# - change number of targets in FOV

import struct
import random
import time
import math
import threading
import codecs
import json
try:
    import socketserver
except ImportError:
    import socketserver as SocketServer


class sonar_prop:
    # change these to reflect your own system as needed
    ping_id = 100
    next_id = 10
    min_range_m = 0
    max_range_m = 50
    min_angle_m = 0
    max_angle_m = 120
    min_target = .5
    max_target = 4
    max_target_strength = 5
    min_target_strength = 1
    max_ts_perturb = 0.1

    ping_rate_hz = 2
    host = 'localhost'
    port = 5000
    # for server client interaction
    track_message = ''
    track_event = threading.Event()
    end_event = threading.Event()


class track ():
    def __init__(self):
        self.id = sonar_prop.next_id
        sonar_prop.next_id += 1
        self.min_range_m = sonar_prop.min_range_m
        self.max_range_m = sonar_prop.max_range_m
        self.min_angle_m = sonar_prop.min_angle_m
        self.max_angle_m = sonar_prop.max_angle_m
        self.first_ping = sonar_prop.ping_id
        self.pings_visible = 0
        self.last_pos_range = random.uniform(self.min_range_m, self.max_range_m)
        self.last_pos_angle = random.uniform(self.min_angle_m, self.max_angle_m)
        self.width = random.uniform(sonar_prop.min_target, sonar_prop.max_target)
        self.height = self.width / 3
        self.speed_mps = random.uniform(1, 2) * self.width
        self.size_sq_m = self.width * self.height
        self.last_update = time.time()
        self.target_strength = sonar_prop.max_target_strength*random.random() - sonar_prop.min_target_strength

        print('Generated track ', self.id)

    def get_buffer(self):
        # 'ffiffffffffffH'
        msg = {"speed_mps": self.speed_mps,
               "min_angle_m": self.min_angle_m,
               "first_ping": self.first_ping,
               "min_range_m": self.min_range_m,
               "target_strength": self.target_strength,
               "last_pos_angle": self.last_pos_angle,
               "max_angle_m": self.max_angle_m,
               "max_range_m": self.max_range_m,
               "last_pos_range": self.last_pos_range,
               "width": self.width,
               "size_sq_m": self.size_sq_m,
               "pings_visible": self.pings_visible,
               "height": self.height,
               "id": self.id}
        # print(msg)
        return msg

    def perturb(self):
        t = time.time()
        dt = t - self.last_update
        self.last_update = t

        # move target based on velocity
        r = self.speed_mps * dt
        theta = random.randint(0, 360)
        dx = r * math.cos(math.radians(theta))
        dy = r * math.sin(math.radians(theta))

        x = self.last_pos_range * math.cos(
                    math.radians(self.last_pos_angle)) + dx
        y = self.last_pos_range * math.sin(
                    math.radians(self.last_pos_angle)) + dy

        self.last_pos_range = math.sqrt(x * x + y * y)
        self.last_pos_angle = math.degrees(math.atan(float(y) / x))

        # toggle target strength
        d_ts = sonar_prop.max_ts_perturb
        self.target_strength = self.target_strength + random.uniform(-1*d_ts, d_ts)

        # is it in view?
        if self.last_pos_angle < sonar_prop.min_angle_m or self.last_pos_angle > sonar_prop.max_angle_m:
            return False
        if self.last_pos_range < sonar_prop.min_range_m or self.last_pos_range > sonar_prop.max_range_m:
            return False

        # toggle its speed
        self.speed_mps *= random.uniform(-.1, .1)
        if self.speed_mps <= 0:
            self.speed_mps = 1

        self.pings_visible += 1
        return True


class server(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


class handler(socketserver.BaseRequestHandler):

    def handle(self):
        while sonar_prop.track_event.wait():
            self.request.sendall(sonar_prop.track_message)
            print(("sent tracks for ping", sonar_prop.ping_id))
            sonar_prop.end_event.wait()

        print("dropped out")


def format_json(tracks):
    msg = []
    for t in tracks:
        msg.append(t.get_buffer())

    msg = json.dumps(msg)
    msg = codecs.latin_1_encode(msg)[0]
    frmt = "=%ds" % len(msg)
    msg = struct.pack(frmt, msg)
    return msg


if __name__ == "__main__":
    # probability of generating a new track if n tracks < max_targets
    track_prob = 25
    # maximum number of targets allowed
    max_targets = 5
    # maximum number of pings @ max_targets before removing 1 target at random
    max_pings = 300

    # start with one track
    tracks = [track()]

    srv = server((sonar_prop.host, sonar_prop.port), handler)
    srv.allow_reuse_address = True
    srv_thread = threading.Thread(target=srv.serve_forever)
    srv_thread.daemon = True
    srv_thread.start()

    counts = 0

    while True:
        # create track packet to write

        msg = format_json(tracks)

        sonar_prop.track_message = msg
        sonar_prop.ping_id += 1

        tracks = [t for t in tracks if t.perturb()]
        print("n tracks = ", len(tracks))

        # if there are fewer tracks than the specified maximum, generate a new
        # track (25% of the time). If more than 300 pings have elapsed with no
        # changes in the tracks, randomly remove one track.

        if len(tracks) < max_targets:
            if random.randint(1, 100) < track_prob:
                tracks.append(track())
                counts = 0

        elif counts > max_pings:
            del tracks[random.randint(0, len(tracks) - 1)]
            counts = 0

        else:
            counts += 1

        sonar_prop.end_event.clear()
        sonar_prop.track_event.set()
        time.sleep(1.0 / sonar_prop.ping_rate_hz)
        sonar_prop.track_event.clear()
        sonar_prop.end_event.set()
