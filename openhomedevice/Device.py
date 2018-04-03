import requests
import re

from openhomedevice.RootDevice import RootDevice
from openhomedevice.TrackInfoParser import TrackInfoParser
from openhomedevice.Soap import soapRequest, subscribeRequest, unsubscribeRequest, renewSubscriptionRequest

import xml.etree.ElementTree as etree

import socket
import threading
import time

class Device(object):

    sidToSocket = {}

    def __init__(self, location):
        xmlDesc = requests.get(location).text.encode('utf-8')
        self.rootDevice = RootDevice(xmlDesc, location)

    def Uuid(self):
        return self.rootDevice.Device().Uuid()

    def HasTransportService(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Transport")
        return service is not None

    def Name(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Product")
        product = soapRequest(service.ControlUrl(), service.Type(), "Product", "")

        productXml = etree.fromstring(product)
        return productXml[0].find("{%s}ProductResponse/Name" % service.Type()).text.encode('utf-8')

    def Room(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Product")
        product = soapRequest(service.ControlUrl(), service.Type(), "Product", "")

        productXml = etree.fromstring(product)
        return productXml[0].find("{%s}ProductResponse/Room" % service.Type()).text.encode('utf-8')

    def SetStandby(self, standbyRequested):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Product")

        valueString = None
        if standbyRequested:
            valueString = "<Value>1</Value>"
        else:
            valueString = "<Value>0</Value>"
        soapRequest(service.ControlUrl(), service.Type(), "SetStandby", valueString)

    def IsInStandby(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Product")
        standbyState = soapRequest(service.ControlUrl(), service.Type(), "Standby", "")

        standbyStateXml = etree.fromstring(standbyState)
        return standbyStateXml[0].find("{%s}StandbyResponse/Value" % service.Type()).text == "1"

    def TransportState(self):
        if self.HasTransportService():
            service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Transport")
            transportState = soapRequest(service.ControlUrl(), service.Type(), "TransportState", "")

            transportStateXml = etree.fromstring(transportState)
            return transportStateXml[0].find("{%s}TransportStateResponse/State" % service.Type()).text
        else:
            source = self.Source()
            if source["type"] == "Radio":
                return self.RadioTransportState()
            if source["type"] == "Playlist":
                return self.PlaylistTransportState()
            return ""

    def Play(self):
        if self.HasTransportService():
            self.PlayTransport()
        else:
            source = self.Source()
            if source["type"] == "Radio":
                return self.PlayRadio()
            if source["type"] == "Playlist":
                return self.PlayPlaylist()

    def PlayMedia(self, track_details):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Radio")

        didl_lite = '<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/">' \
                    '<item id="" parentID="" restricted="True">' \
                    '<dc:title>' + track_details['title'] + '</dc:title>' \
                    '<res protocolInfo="*:*:*:*">' + track_details['uri'] + '</res>' \
                    '<upnp:albumArtURI>' + track_details['albumArtwork'] + '</upnp:albumArtURI>' \
                    '<upnp:class>object.item.audioItem</upnp:class>' \
                    '</item>' \
                    '</DIDL-Lite>'

        channelValue = ("<Uri>%s</Uri><Metadata>%s</Metadata>" % (track_details["uri"], didl_lite))
        soapRequest(service.ControlUrl(), service.Type(), "SetChannel", channelValue)

        self.PlayRadio()

    def Stop(self):
        if self.HasTransportService():
            self.StopTransport()
        else:
            source = self.Source()
            if source["type"] == "Radio":
                return self.StopRadio()
            if source["type"] == "Playlist":
                return self.StopPlaylist()

    def Pause(self):
        if self.HasTransportService():
            self.PauseTransport()
        else:
            source = self.Source()
            if source["type"] == "Radio":
                return self.StopRadio()
            if source["type"] == "Playlist":
                return self.PausePlaylist()

    def Skip(self, offset):
        if self.HasTransportService():
            service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Transport")

            command = None
            if offset > 0:
                command = "SkipNext"
            else:
                command = "SkipPrevious"

            for x in range(0, abs(offset)):
                soapRequest(service.ControlUrl(), service.Type(), command, "")
        else:
            source = self.Source()
            if source["type"] == "Playlist":
                service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Playlist")

                command = None
                if offset > 0:
                    command = "Next"
                else:
                    command = "Previous"

                for x in range(0, abs(offset)):
                    soapRequest(service.ControlUrl(), service.Type(), command, "")

    def RadioTransportState(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Radio")
        transportState = soapRequest(service.ControlUrl(), service.Type(), "TransportState", "")

        transportStateXml = etree.fromstring(transportState)
        return transportStateXml[0].find("{%s}TransportStateResponse/Value" % service.Type()).text

    def PlaylistTransportState(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Playlist")
        transportState = soapRequest(service.ControlUrl(), service.Type(), "TransportState", "")

        transportStateXml = etree.fromstring(transportState)
        return transportStateXml[0].find("{%s}TransportStateResponse/Value" % service.Type()).text

    def PlayTransport(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Transport")
        soapRequest(service.ControlUrl(), service.Type(), "Play", "")

    def PlayRadio(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Radio")
        soapRequest(service.ControlUrl(), service.Type(), "Play", "")

    def PlayPlaylist(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Playlist")
        soapRequest(service.ControlUrl(), service.Type(), "Play", "")

    def PauseTransport(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Transport")
        soapRequest(service.ControlUrl(), service.Type(), "Pause", "")

    def PausePlaylist(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Playlist")
        soapRequest(service.ControlUrl(), service.Type(), "Pause", "")

    def StopTransport(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Transport")
        soapRequest(service.ControlUrl(), service.Type(), "Stop", "")

    def StopRadio(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Radio")
        soapRequest(service.ControlUrl(), service.Type(), "Stop", "")

    def StopPlaylist(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Playlist")
        soapRequest(service.ControlUrl(), service.Type(), "Stop", "")

    def Source(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Product")
        source = soapRequest(service.ControlUrl(), service.Type(), "SourceIndex", "")

        sourceXml = etree.fromstring(source)
        sourceIndex = sourceXml[0].find("{%s}SourceIndexResponse/Value" % service.Type()).text

        sourceInfo = soapRequest(service.ControlUrl(), service.Type(), "Source", ("<Index>%s</Index>" % int(sourceIndex)))
        sourceInfoXml = etree.fromstring(sourceInfo)

        sourceName = sourceInfoXml[0].find("{%s}SourceResponse/Name" % service.Type()).text
        sourceType = sourceInfoXml[0].find("{%s}SourceResponse/Type" % service.Type()).text

        return {
            "type": sourceType,
            "name": sourceName
        }

    def VolumeEnabled(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Volume")
        return service is not None

    def VolumeLevel(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Volume")

        if service is None:
            return None

        volume = soapRequest(service.ControlUrl(), service.Type(), "Volume", "")

        volumeXml = etree.fromstring(volume)
        return int(volumeXml[0].find("{%s}VolumeResponse/Value" % service.Type()).text)

    def IsMuted(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Volume")

        if service is None:
            return None

        mute = soapRequest(service.ControlUrl(), service.Type(), "Mute", "")

        muteXml = etree.fromstring(mute)
        return muteXml[0].find("{%s}MuteResponse/Value" % service.Type()).text == "true"

    def SetVolumeLevel(self, volumeLevel):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Volume")
        valueString = ("<Value>%s</Value>" % int(volumeLevel))
        soapRequest(service.ControlUrl(), service.Type(), "SetVolume", valueString)

    def IncreaseVolume(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Volume")
        soapRequest(service.ControlUrl(), service.Type(), "VolumeInc", "")

    def DecreaseVolume(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Volume")
        soapRequest(service.ControlUrl(), service.Type(), "VolumeDec", "")

    def SetMute(self, muteRequested):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Volume")
        valueString = None
        if muteRequested:
            valueString = "<Value>1</Value>"
        else:
            valueString = "<Value>0</Value>"
        soapRequest(service.ControlUrl(), service.Type(), "SetMute", valueString)

    def SetSource(self, index):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Product")
        valueString = ("<Value>%s</Value>" % int(index))
        soapRequest(service.ControlUrl(), service.Type(), "SetSourceIndex", valueString)

    def Sources(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Product")
        sources = soapRequest(service.ControlUrl(), service.Type(), "SourceXml", "")

        sourcesXml = etree.fromstring(sources)
        sourcesList = sourcesXml[0].find("{%s}SourceXmlResponse/Value" % service.Type()).text

        sourcesListXml = etree.fromstring(sourcesList)

        sources = []
        index = 0
        for sourceXml in sourcesListXml:
            visible = sourceXml.find("Visible").text == "true"
            if visible:
                sources.append({
                    "index": index,
                    "name": sourceXml.find("Name").text,
                    "type": sourceXml.find("Type").text
                })
            index = index + 1
        return sources

    def TrackInfo(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Info")
        trackInfoString = soapRequest(service.ControlUrl(), service.Type(), "Track", "")

        trackInfoParser = TrackInfoParser(trackInfoString)

        return trackInfoParser.TrackInfo()

    def GetConfigurationKeys(self):
        import json
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Config")
        keys = soapRequest(service.ControlUrl(), service.Type(), "GetKeys", "")

        keysXml = etree.fromstring(keys)
        keysArray = keysXml[0].find("{%s}GetKeysResponse/KeyList" % service.Type()).text

        return json.loads(keysArray)

    def GetConfiguration(self, key):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Config")
        keyString = ("<Key>%s</Key>" % key)
        configurationValue = soapRequest(service.ControlUrl(), service.Type(), "GetValue", keyString)

        configurationValueXml = etree.fromstring(configurationValue)
        return configurationValueXml[0].find("{%s}GetValueResponse/Value" % service.Type()).text

    def SetConfiguration(self, key, value):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Config")
        configValue = ("<Key>%s</Key><Value>%s</Value>" % (key, value))
        soapRequest(service.ControlUrl(), service.Type(), "SetValue", configValue)
        
    def GetLog(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Debug")
        return soapRequest(service.ControlUrl(), service.Type(), "GetLog", "").decode('utf-8').split("\n")

    def SubscribeTrackInfo(self, callbackHost, callbackPort, callbackFunction, timespan):
        """Subscribe to track info events.
        
        :param callbackHost: The host name or ip address of this machine. Will be used for notications
        :param callbackPort: The port
        :param callbackFunction: The function that sould be called in case of event notifications
        :param timespan: Timespan of the subscription. Nevertheless, the subscription will be renewed until unsubscribing
        :returns: Subscription identifier (SID). Empty if subscribing fails.
        """
        return self.__SubscribeEvent("urn:av-openhome-org:serviceId:Info", callbackHost, callbackPort, callbackFunction, timespan)
        
    def UnsubscribeTrackInfo(self, sid):
        """Unsubscribe from track info events.
        
        :param sid: The subscription identifier to unsubscribe from
        """
        self.__UnsubscribeEvent("urn:av-openhome-org:serviceId:Info", sid)
        
    def SubscribeTime(self, callbackHost, callbackPort, callbackFunction, timespan):
        """Unsubscribe to time events.
        
        :param callbackHost: The host name or ip address of this machine. Will be used for notications
        :param callbackPort: The port
        :param callbackFunction: The function that sould be called in case of event notifications
        :param timespan: Timespan of the subscription. Nevertheless, the subscription will be renewed until unsubscribing
        :returns: Subscription Identifier (SID). Empty if subscribing fails.
        """
        return self.__SubscribeEvent("urn:av-openhome-org:serviceId:Time", callbackHost, callbackPort, callbackFunction, timespan)
        
    def UnsubscribeTime(self, sid):
        """Unsubscribe from time events.
        
        :param sid: The subscription identifier to unsubscribe from
        """
        self.__UnsubscribeEvent("urn:av-openhome-org:serviceId:Time", sid)
    
    def __SubscribeEvent(self, serviceUrl, callbackHost, callbackPort, callbackFunction, timespan):
        """Subscribe to events of given type.
        
        This method subscribes to the given event type and listens in a separate thread for notifications.
        Since subscriptions may expire the subscription is renewed before the given timespan ihas elapsed.
        """
        if timespan <= 60:
            timespan = 60
        
        # Init socket, so that we get the response of the subscribe request.
        # Later the socket is given to the subscription listener for response handling
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((callbackHost, callbackPort))
        sock.listen(0)
        
        service = self.rootDevice.Device().Service(serviceUrl)
        response = subscribeRequest(service.EventSubUrl(), callbackHost, callbackPort, timespan)
        if response.status_code == 200:
            subscribeSID = response.headers['SID']
            self.sidToSocket[subscribeSID] = sock
            subscribeTimeout = int(response.headers['TIMEOUT'].split('-')[1])
            if subscribeTimeout >= 30:
                subscribeTimeout = subscribeTimeout - 30
            else:
                subscribeTimeout = 30
            threading.Thread(target = self.__SubscribeListen, args = (sock, subscribeSID, callbackHost, callbackPort, callbackFunction)).start()
            threading.Timer(subscribeTimeout, self.__RenewSubscription, args = (service.EventSubUrl(), subscribeSID, timespan, subscribeTimeout)).start()
            return subscribeSID
        else:
            return ""
        
    def __UnsubscribeEvent(self, serviceUrl, sid):
        """Unsubscribes from events with the given sid."""
        service = self.rootDevice.Device().Service(serviceUrl)
        self.sidToSocket[sid].shutdown(socket.SHUT_RDWR)
        self.sidToSocket[sid].close()
        self.sidToSocket.pop(sid)

    def __RenewSubscription(self, eventLocation, subscribeSID, timespan, subscribeTimeout):
        """Renew the subscription.
        
        The subscription is renewed periodically, given the timespan parameter.
        The subscription may be ended by unsubscribing.
        """
        response = renewSubscriptionRequest(eventLocation, subscribeSID, timespan)
        if response.status_code == 200:
            threading.Timer(subscribeTimeout, self.__RenewSubscription, args = (eventLocation, subscribeSID, timespan, subscribeTimeout)).start()

    def __SubscribeListen(self, sock, subscribeSID, callbackHost, callbackPort, callbackFunction):
        """Listen on the given socket and call callbackFunction with the response."""
        while True:
            try:
                client, address = sock.accept()
            except:
                break
            client.setblocking(0)
            try:
                data = self.__recv_timeout(client)
                if data:
                    #decode it to string, take only the body
                    httpString = bytes.decode(data).split('\r\n\r\n')
                    properties = {}
                    try:
                        # Fetch SID from HTTP header, check if corresponds to our subscription SID
                        responseSID = httpString[0].split('SID: ')[1].split('\r\n')[0]
                        if responseSID == subscribeSID:
                            for property in etree.fromstring(httpString[1]).iter('{urn:schemas-upnp-org:event-1-0}property'):
                                if 'Metadata' != property[0].tag or not property[0].text:
                                    properties[property[0].tag] = property[0].text
                                else:
                                    properties['Metadata'] = self.getTrackMetadata(property[0].text)
                            callbackFunction(properties)
                            client.send(b'HTTP/1.1 200 OK\r\n\r\n')
                    except:
                        pass
            finally:
                client.shutdown(socket.SHUT_RDWR)
                client.close()

    def __recv_timeout(self, the_socket, timeout = 1):
        """Read data from the socket.
        
        Reading is stopped if no more data is received within given timeout.
        """
        total_data=[];
        data='';
        
        begin=time.time()
        while True:
            if total_data and time.time()-begin > timeout:
                break
            elif time.time()-begin > timeout*2:
                break
            
            try:
                data = the_socket.recv(4096)
                if data:
                    total_data.append(data)
                    begin=time.time()
                else:
                    time.sleep(0.1)
            except:
                pass
        
        return b''.join(total_data)
