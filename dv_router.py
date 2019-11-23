"""
Your awesome Distance Vector router for CS 168
"""

import sim.api as api
import sim.basics as basics
import time


# We define infinity as a distance of 16.
INFINITY = 16
TimeDiff = 15

class DVRouter (basics.DVRouterBase):
  #NO_LOG = True # Set to True on an instance to disable its logging
  POISON_MODE = True # Can override POISON_MODE here
  #DEFAULT_TIMER_INTERVAL = 5 # Can override this yourself for testing

  def __init__ (self):
    """
    Called when the instance is initialized.

    You probably want to do some additional initialization here.
    """
    self.start_timer() # Starts calling handle_timer() at correct rate
    self.neighbours = dict()
    self.routesToDest = dict()
    self.hosts = dict()

  def handle_link_up (self, port, latency):
    """
    Called by the framework when a link attached to this Entity goes up.

    The port attached to the link and the link latency are passed in.
    """
    self.neighbours[port] = latency
    for dest in self.routesToDest:
      packet = basics.RoutePacket(dest, self.routesToDest[dest][1])
      self.send(packet, port, False)
      

  def handle_link_down (self, port):
    """
    Called by the framework when a link attached to this Entity does down.

    The port number used by the link is passed in.
    """
    for dest in self.hosts.keys():
      currPort = self.hosts[dest][0]
      if currPort == port:
        del self.hosts[dest]
    
    deleteDests = set()
    for dest in self.routesToDest:
      currPort = self.routesToDest[dest][0]
      
      if currPort == port:

        if dest in self.hosts:
          self.routesToDest[dest] = self.hosts[dest]
          self.send(packet, self.routesToDest[dest][0], True)
        else:
          self.sendPoison(dest)
          deleteDests.add(dest)


    for dest in deleteDests:
      del self.routesToDest[dest]

    del self.neighbours[port]

  def handle_rx (self, packet, port):
    """
    Called by the framework when this Entity receives a packet.

    packet is a Packet (or subclass).
    port is the port number it arrived on.

    You definitely want to fill this in.
    """
    
    #self.log("RX %s on %s (%s)", packet, port, api.current_time())
    if isinstance(packet, basics.RoutePacket):

      dest = packet.destination
      newLatency = self.neighbours[port] + packet.latency

      oldLatency = INFINITY
      if dest in self.routesToDest:
        oldLatency = self.routesToDest[dest][1]


      if dest not in self.routesToDest or newLatency <= oldLatency or (dest in self.routesToDest and self.routesToDest[dest][0] == port):
        self.routesToDest[dest] = (port, newLatency, api.current_time(), False)
        
        
      if dest in self.hosts and self.hosts[dest][1] <= self.routesToDest[dest][1]:
        self.routesToDest[dest] = self.hosts[dest]
      
      if oldLatency != self.routesToDest[dest][1]:
        newPacket = basics.RoutePacket(dest, self.routesToDest[dest][1])
        self.send(newPacket, port, True)

    elif isinstance(packet, basics.HostDiscoveryPacket):
      self.routesToDest[packet.src] = (port, self.neighbours[port], api.current_time(), True)
      self.send(basics.RoutePacket(packet.src, self.neighbours[port]), port, True)
      self.hosts[packet.src] = (port, self.neighbours[port], api.current_time(), True)
    else:
      # Totally wrong behavior for the sake of demonstration only: send
      # the packet back to where it came from!

      
      reciever = packet.dst
      if reciever in self.routesToDest:
        latency = self.routesToDest[reciever][1]

        if latency < INFINITY and self.routesToDest[reciever][0] != port:
          self.send(packet, self.routesToDest[reciever][0], False)
          return

      if reciever in self.hosts:
        self.routesToDest[reciever] = self.hosts[reciever]
        latency = self.routesToDest[reciever][1]

        if latency < INFINITY and self.routesToDest[reciever][0] != port:
          self.send(packet, self.hosts[reciever][0], False)


  def handle_timer (self):
    """
    Called periodically.

    When called, your router should send tables to neighbors.  It also might
    not be a bad place to check for whether any entries have expired.
    """

    #self.log("handle_timer " + str(len(self.routesToDest)))
    deleteDests = set()
    for dest in self.routesToDest:
      recievedTime = self.routesToDest[dest][2]

      if api.current_time() - recievedTime <= TimeDiff or self.routesToDest[dest][3]:
        latency = self.routesToDest[dest][1]
        packet = basics.RoutePacket(dest, latency)
        port = self.routesToDest[dest][0]
        self.send(packet, port, True)
      else:
        if dest in self.hosts:
          packet = basics.RoutePacket(dest, self.hosts[dest][1])
          self.send(packet, self.hosts[dest][0], True)
          self.routesToDest[dest] = self.hosts[dest]
        else:
          deleteDests.add(dest)
          self.sendPoison(dest)

    for dest in deleteDests:
      del self.routesToDest[dest]

  def sendPoison(self, destination):
    if self.POISON_MODE:
      packet = basics.RoutePacket(destination, INFINITY)
      self.send(packet, flood=True)   

  