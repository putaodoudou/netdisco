"""
Adds support for discovery using GDM (Good Day Mate),
an in-house developped multicast protocol by Plex.

Inspired by
  hippojay's plexGDM:
  https://github.com/hippojay/script.plexbmc.helper/resources/lib/plexgdm.py
  iBaa's PlexConnect: https://github.com/iBaa/PlexConnect/PlexAPI.py
"""
import threading
import socket


class GDM(object):
    """ Base class to discover GDM services. """

    def __init__(self):
        self.entries = []
        self.last_scan = None
        self._lock = threading.RLock()

    def scan(self):
        ''' Scan the network. '''
        with self._lock:
            self.update()

    def all(self):
        """
        Returns all found entries.
        Will scan for entries if not scanned recently.
        """
        self.scan()
        return list(self.entries)

    def find_by_content_type(self, value):
        '''
        Return a list of entries that match the content_type
        '''
        self.scan()
        return [entry for entry in self.entries
                if value in entry['data']['Content_Type']]

    def find_by_data(self, values):
        '''
        Return a list of entries that match the search parameters
        '''
        self.scan()
        return [entry for entry in self.entries
                if (item in values.items() for item in entry['data'].items())]

    def update(self):
        ''' Scans for new GDM services. '''
        gdm_ip = '239.0.0.250'  # multicast to PMS
        gdm_port = 32414
        gdm_msg = 'M-SEARCH * HTTP/1.0'.encode('ascii')
        gdm_timeout = 1

        self.entries = []

        # setup socket for discovery -> multicast message
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(gdm_timeout)

        # Set the time-to-live for messages for local network
        sock.setsockopt(socket.IPPROTO_IP,
                        socket.IP_MULTICAST_TTL,
                        gdm_timeout)

        try:
            # Send data to the multicast group
            sock.sendto(gdm_msg, (gdm_ip, gdm_port))

            # Look for responses from all recipients
            while True:
                try:
                    data, server = sock.recvfrom(1024)
                    data = data.decode('ascii')
                    if '200 OK' in data.splitlines()[0]:
                        data = {k: v.strip() for (k, v) in (
                            line.split(':') for line in
                            data.splitlines() if ':' in line)}
                        self.entries.append({'data': data,
                                             'from': server})
                except socket.timeout:
                    break
        finally:
            sock.close()


if __name__ == "__main__":
    from pprint import pprint

    # pylint: disable=invalid-name
    gdm = GDM()

    pprint("Scanning GDM..")
    gdm.update()
    pprint(gdm.entries)