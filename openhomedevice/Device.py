import requests

from openhomedevice.RootDevice import RootDevice
from openhomedevice.Soap import soapRequest, subscribeRequest, renewSubscriptionRequest

import xml.etree.ElementTree as etree

import socket
import threading
import time

class Device(object):

    def __init__(self, location):
        xmlDesc = requests.get(location).text.encode('utf-8')
        self.rootDevice = RootDevice(xmlDesc, location)

    def Uuid(self):
        return self.rootDevice.Device().Uuid()

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
        return standbyStateXml[0].find("{%s}StandbyResponse/Value" % service.Type()).text == "true"

    def TransportState(self):
        source = self.Source()
        if source["type"] == "Radio":
            return self.RadioTransportState()
        if source["type"] == "Playlist":
            return self.PlaylistTransportState()
        return ""

    def Play(self):
        source = self.Source()
        if source["type"] == "Radio":
            return self.PlayRadio()
        if source["type"] == "Playlist":
            return self.PlayPlaylist()

    def Stop(self):
        source = self.Source()
        if source["type"] == "Radio":
            return self.StopRadio()
        if source["type"] == "Playlist":
            return self.StopPlaylist()

    def Pause(self):
        source = self.Source()
        if source["type"] == "Radio":
            return self.StopRadio()
        if source["type"] == "Playlist":
            return self.PausePlaylist()

    def Skip(self, offset):
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

    def PlayRadio(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Radio")
        soapRequest(service.ControlUrl(), service.Type(), "Play", "")

    def StopRadio(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Radio")
        soapRequest(service.ControlUrl(), service.Type(), "Stop", "")

    def PlayPlaylist(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Playlist")
        soapRequest(service.ControlUrl(), service.Type(), "Play", "")

    def PausePlaylist(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Playlist")
        soapRequest(service.ControlUrl(), service.Type(), "Pause", "")

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
        return service != None

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
        trackInfo = soapRequest(service.ControlUrl(), service.Type(), "Track", "")
        
        trackInfoXml = etree.fromstring(trackInfo)
        metadata = trackInfoXml[0][0].find("Metadata").text

        return self.getTrackMetadata(metadata)
        
    def getTrackMetadata(self, metadata):
        if metadata is None or not metadata:
            return {}

        metadataXml = etree.fromstring(metadata)
        itemElement = metadataXml.find("{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}item")
        
        albumArt = itemElement.find("{urn:schemas-upnp-org:metadata-1-0/upnp/}albumArtURI")
        album = itemElement.find("{urn:schemas-upnp-org:metadata-1-0/upnp/}album")
        artist = itemElement.find("{urn:schemas-upnp-org:metadata-1-0/upnp/}artist")
        title = itemElement.find("{http://purl.org/dc/elements/1.1/}title")

        trackDetails = {}

        trackDetails['title'] =  title.text if title != None else None
        trackDetails['album'] =  album.text if album != None else None
        trackDetails['albumArt'] =  albumArt.text if albumArt != None else None
        trackDetails['artist'] =  artist.text if artist != None else None
        
        return trackDetailsOB
        
    def SubscribeTrackInfo(self, callbackHost, callbackPort, callbackFunction, timespan):
        if timespan <= 60:
            timespan = 60
        threading.Thread(target = self.SubscribeListen, args = (callbackHost, callbackPort, callbackFunction)).start()
        
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Info")
        response = subscribeRequest(service.EventSubUrl(), callbackHost, callbackPort, timespan)
        if response.status_code == 200:
            self.subscribeSID = response.headers['SID']
            self.subscribeTimeout = int(response.headers['TIMEOUT'].split('-')[1])
            if self.subscribeTimeout >= 30:
                self.subscribeTimeout = self.subscribeTimeout - 30
            else:
                self.subscribeTimeout = 30
            threading.Timer(self.subscribeTimeout, self.RenewSubscription, args = (service.EventSubUrl(),)).start()

    def RenewSubscription(self, eventLocation):
        renewSubscriptionRequest(eventLocation, self.subscribeSID, self.subscribeTimeout)
        threading.Timer(self.subscribeTimeout, self.RenewSubscription, args = (eventLocation,)).start()

    def SubscribeListen(self, callbackHost, callbackPort, callbackFunction):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((callbackHost, callbackPort))
        sock.listen(0)
        while True:
            client, address = sock.accept()
            client.setblocking(0)
            try:
                data = self.recv_timeout(client)
                if data:
                    #decode it to string, takeonly the body
                    httpString = bytes.decode(data).split('\r\n\r\n')
                    properties = {}
                    for property in etree.fromstring(httpString[1]).iter('{urn:schemas-upnp-org:event-1-0}property'):
                        if 'Metadata' != property[0].tag or not property[0].text:
                            properties[property[0].tag] = property[0].text
                        else:
                            properties['Metadata'] = self.getTrackMetadata(property[0].text)
                    callbackFunction(properties)
                    client.send(b'HTTP/1.1 200 OK\nContent-Type: text/html\nContent-Length: 0\n\n')
            finally:
                client.shutdown(socket.SHUT_RDWR)
                client.close()

    def recv_timeout(self, the_socket, timeout = 2):
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
