from struct import *
import random
import time
import math
import threading
import codecs
try:
    import socketserver
except ImportError:
    import socketserver as SocketServer

class sonar_prop:
    # change these to reflect your own system as needed
    ping_id = 100
    next_id = 10
    min_range_m = 0
    max_range_m = 400
    min_angle_m = 15
    max_angle_m = 165
    min_target = .5
    max_target = 4
    ping_rate_hz = 2
    host = 'localhost'
    port = 5000
    # for server client interaction
    track_message = ''
    track_event = threading.Event()
    end_event = threading.Event()

class track ():
    def __init__(self ):
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
        print(("my angle is:", self.last_pos_angle))
        self.width = random.uniform(sonar_prop.min_target, sonar_prop.max_target)
        self.height = self.width / 3
        self.speed_mps = random.uniform(1, 2) * self.width
        self.size_sq_m = self.width * self.height
        self.last_update = time.time();

    def get_buffer(self):
        return pack('HffffffiHffff', self.id, self.size_sq_m,self.speed_mps, self.min_range_m, self.max_range_m,
                   self.min_angle_m, self.max_angle_m, self.first_ping, self.pings_visible, self.last_pos_range,
                   self.last_pos_angle, self.width, self.height)

    def perturb(self):
        t = time.time()
        dt = t - self.last_update
        self.last_update = t


        # move target based on velocity
        r = self.speed_mps * dt
        theta = random.randint(0, 360)
        dx = r * math.cos(math.radians(theta))
        dy = r * math.sin(math.radians(theta))

        x = self.last_pos_range * math.cos(math.radians(self.last_pos_angle)) + dx
        y = self.last_pos_range * math.sin(math.radians(self.last_pos_angle)) + dy
        self.last_pos_range = math.sqrt(x * x + y * y)
        self.last_pos_angle = math.degrees(math.atan(float(y) / x))

        # is it in view?
        if self.last_pos_angle < sonar_prop.min_angle_m or self.last_pos_angle > sonar_prop.max_angle_m:
            return False
        if self.last_pos_range < sonar_prop.min_range_m or self.last_pos_range > sonar_prop.max_range_m:
            return False

        # toggle it's speed
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

if __name__ == "__main__":
    max_targets = 5 # arbitrary
    tracks = [track(), track()]

    srv = server((sonar_prop.host, sonar_prop.port), handler)
    srv.allow_reuse_address=True
    srv_thread = threading.Thread(target=srv.serve_forever)
    srv_thread.daemon = True
    srv_thread.start()

    while True:
        # create track packet to write
        msg = codecs.latin_1_encode('')[0]
        for t in tracks:
            msg += t.get_buffer()

        sonar_prop.track_message = msg
        sonar_prop.ping_id += 1

        tracks = [t for t in tracks if t.perturb()]
        print(("tracks:", len(tracks)))
        if len(tracks) < sonar_prop.max_target:
            if random.randint(1, 100) > 25:
                tracks.append(track())

        sonar_prop.end_event.clear()
        sonar_prop.track_event.set()
        time.sleep(1.0 / sonar_prop.ping_rate_hz)
        sonar_prop.track_event.clear()
        sonar_prop.end_event.set()
