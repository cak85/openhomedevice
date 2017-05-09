import requests
import socket

def soapRequest(location, service, fnName, fnParams):
    bodyString = '<?xml version="1.0"?>'
    bodyString += '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">'
    bodyString += '  <s:Body s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">'
    bodyString += '    <u:' + fnName + ' xmlns:u="' + service + '">'
    bodyString += '      ' + fnParams
    bodyString += '    </u:' + fnName + '>'
    bodyString += '  </s:Body>'
    bodyString += '</s:Envelope>'

    headers = {
        'Content-Type': 'text/xml',
        'Accept': 'text/xml',
        'SOAPAction': '\"' + service + '#' + fnName + '\"'
    }

    res = requests.post(location, data=bodyString, headers=headers)
    res.encoding = 'utf-8'

    return res.text.encode('utf-8')

def subscribeRequest(location, callbackHost, callbackPort, subscribeTimeout):
    headers = {
        'Timeout': 'Second-' + str(subscribeTimeout),
        'Callback': '<http://' + callbackHost + ':' + str(callbackPort) + '>',
        'NT': 'upnp:event'
    }

    res = requests.request(method = 'SUBSCRIBE', url = location, headers = headers)
    res.encoding = 'utf-8'

    return res
    
def renewSubscriptionRequest(location, sid, subscribeTimeout):
    headers = {
        'SID': sid,
        'Timeout': 'Second-' + str(subscribeTimeout)
    }

    res = requests.request(method = 'SUBSCRIBE', url = location, headers = headers)
    res.encoding = 'utf-8'

    return res
