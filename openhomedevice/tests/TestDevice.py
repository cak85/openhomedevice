import socket
import threading
from unittest import TestCase
from unittest.mock import patch

from openhomedevice.Device import Device


class TestDevice(TestCase):
    
    ownIp = "127.0.0.1"
    ownAddr = "http://" + ownIp
    port = 55180
    deviceUrl = ownAddr + ":55178/device.xml"
    deviceXml = "<?xml version=\"1.0\"?><root xmlns=\"urn:schemas-upnp-org:device-1-0\"><device><serviceList><service><serviceType>urn:schemas-upnp-org:service:RenderingControl:1</serviceType><serviceId>urn:upnp-org:serviceId:RenderingControl</serviceId><SCPDURL>/scpd/RenderingControl.xml</SCPDURL><controlURL>/ctl/RenderingControl</controlURL><eventSubURL>/evt/RenderingControl</eventSubURL></service><service><serviceType>urn:av-openhome-org:service:Info:1</serviceType><serviceId>urn:av-openhome-org:serviceId:Info</serviceId><SCPDURL>/scpd/OHInfo.xml</SCPDURL><controlURL>/ctl/OHInfo</controlURL><eventSubURL>/evt/OHInfo</eventSubURL></service><service><serviceType>urn:av-openhome-org:service:Time:1</serviceType><serviceId>urn:av-openhome-org:serviceId:Time</serviceId><SCPDURL>/scpd/OHTime.xml</SCPDURL><controlURL>/ctl/OHTime</controlURL><eventSubURL>/evt/OHTime</eventSubURL></service></serviceList></device></root>"
    upnpNotify = b'SID: uuid:1\r\nSEQ: 0\r\n\r\n<e:propertyset xmlns:e="urn:schemas-upnp-org:event-1-0">\n<e:property>\n<TrackCount>0</TrackCount>\n</e:property>\n</e:propertyset>\n\n\r\n'

    def testSubscribeAndUnsubscribeForTrackInfo(self):
        with patch('requests.get') as mock_request:
            mock_request.return_value.text = self.deviceXml
            device = Device(self.deviceUrl)
        with patch('requests.request') as mock_request:
            mock_request.return_value.status_code = 200
            mock_request.return_value.headers = {"SID": "uuid:1", "TIMEOUT": "Second-60"}
            f = threading.Event()
            with patch('unittest.mock.Mock', side_effect=lambda *args, **kwargs: f.set()) as mock:
                sid = device.SubscribeTrackInfo(self.ownIp, self.port, mock, 60)
                mock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                mock_socket.connect((self.ownIp, self.port))
                mock_socket.sendall(self.upnpNotify)
                f.wait(5)
                device.UnsubscribeTrackInfo(sid)
                mock.assert_called_once()
