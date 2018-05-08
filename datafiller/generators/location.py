from __future__ import print_function, unicode_literals

import re

from datafiller.generators.numeric import IntGenerator
from datafiller.generators.seed import SeedGenerator

__author__ = "danishabdullah"
__all__ = ('InetGenerator', 'MACGenerator')


class InetGenerator(IntGenerator):
    """Generate Internet addresses.

    - str network: network in which to choose ips
    - int net, mask: ip and mask from 'network'
    - tonet: int to address conversion function
    """
    DIRS = {'inet': str}

    def __init__(self, att, params=None):
        IntGenerator.__init__(self, att, params)
        # get network target and mask
        self.network = self.params.get('inet', ';0.0.0.0/0')
        if len(self.network):
            beg, end = self.network[0] in ',;', self.network[0] in '.;'
        else:
            beg, end, self.network = True, True, ';0.0.0.0/0'
        if beg or end:
            self.network = self.network[1:]
        if self.network.find(':') != -1:
            # IPv6: rely on netaddr, will fail if not available
            from netaddr import IPNetwork, IPAddress
            self.tonet = IPAddress
            if self.network.find('/') == -1:
                self.network += '/64'
            try:
                ip = IPNetwork(self.network)
            except:
                assert False, "{0}: invalid ipv6 {1}".format(self, self.network)
            self.net = ip.first
            self.mask = ip.hostmask.value
        else:
            # IPv4: local implementation, ipaddress is not always available
            self.tonet = lambda i: \
                '.'.join(str(int((i & (255 << n * 8)) / (1 << n * 8))) \
                         for n in range(3, -1, -1))
            if self.network.find('/') == -1:
                self.network += '/24'
            ipv4, m = re.match(r'(.*)/(.*)', self.network).group(1, 2)
            assert re.match(r'(\d+\.){3}\d+$', ipv4), \
                "{0}: invalid ipv4 {1}".format(self, self.network)
            try:
                n, m = 0, int(m)
                assert 0 <= m and m <= 32, \
                    "{0}: ipv4 mask not in 0..32".format(self, m)
                # extract network number
                for i in map(int, re.split('\.', ipv4)):
                    assert 0 <= i and i <= 255, \
                        "{0}: ipv4 byte {1} not in 0..255".format(self, i)
                    n = n * 256 + i
            except:
                assert False, "{0}: invalid ipv4 {1}".format(self, self.network)
            assert 0 <= n and n <= 0xffffffff, \
                "{0}: ipv4 address {1} not on 4 bytes".format(self, n)
            self.mask = (1 << (32 - m)) - 1
            self.net = n & (0xffffffff ^ self.mask)
        # override size & offset if was not set explicitely
        size = self.mask - 1 + int(beg) + int(end)
        if self.size == None:
            assert size > 0, \
                "{0}: empty address range {1}".format(self, self.network)
            self.setSize(size)
        else:
            # ??? fix default size in some cases...
            if self.size > size:
                self.setSize(size)
        if not 'offset' in self.params:
            self.offset = int(not beg)
        self.cleanParams(InetGenerator.DIRS)

    def genData(self):
        return self.tonet(super(InetGenerator, self).genData() + self.net)


# maybe it should rely on IntGenerator?
class MACGenerator(SeedGenerator):
    """Generate MAC Addresses."""
    DIRS = {}

    def __init__(self, att, params=None):
        SeedGenerator.__init__(self, att, params)
        self.cleanParams(MACGenerator.DIRS)

    def genData(self):
        self.reseed()
        return ':'.join(format(self._rand2.randrange(256), '02X') \
                        for i in range(6))
