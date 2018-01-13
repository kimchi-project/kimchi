#Complete Spice Web Client written in HTML5 and Javascript 
Full and complete implementation of the SPICE protocol (by Red Hat) written in HTML5 and JavaScript. It allows any standard HTML5-ready Web Browser to connect to remote 
virtual sessions just by accessing a single URL.

The client can be deployed through a normal web server to connect to spice sessions. To use it you would need to proxy your spice session through a websockets-to-tcp 
proxy like Kanaka, Websockify or similar projects.

NOTE: This project is NOT based on the spice-html5 prototype.

## Features

- Full QXL Support of the entire spice protocol, including clipping, masking, scaling etc (accelerated mode)
- Audio support, but only for raw audio samples, not for celt
- Full KeyBoard support including English, Spanish and Catalan layouts
- Clipboard sharing support with customizble interface
- Video streaming support with excellent performance even at 60fps FHD 1080p
- Extremly high performant LZ decoder with sub <10ms for a FHD 1080P image
- Pure Javascript codec for quic
- Configurable multi core support using webworkers (by default it uses 4 CPU Cores)
- Spice Agent support
- Set resolution support
- Honors spice cache for images, cursors and palettes
- Very low memory footprint for a javascript application like this
- Spice authentication tokens support
- Supports graphic live debugging the spice protocol and to replay packets to fix bugs

##Missing features

There are some SPICE features still to be implemented, the most important ones are:

- Celt or other audio codec
- USB redirection (not possible at browser level, maybe with a plugin?)

##Client System requirements

To get the best result we recommend at least 1GB of ram and at least two cores at 1,5ghz. 

It should work decently on 512mb of ram and 1ghz.

We have made tests in raspberry pi 2 with very good results.

##Network requirements

Only Binary websockets are used to send and receive server data, so you should expect similar network requirements than SPICE itself.
for a normal 1080p session the performance is very good up to 150-200ms of latency and 100kb/s bandwidth.

The network consumption of a spice session depends a lot on the usage patterns.    

##Performance

Writing a web client for a protocol like spice is challenge because of the limited access to system resources like GPU and the way the javascript VM works.

We have spent almost 2 years profiling the entire project. The lz decoder has been optimized to <10Ms for full hd images. Quic codec has been hacked a lot 
to get acceptable performance even being executed in javascript.

We have created a graphic pipeline to remove unnecesary draw operations that are going to be overdrawn at the next known packets. We have minimized the work
for the javascript GC and refined all our canvas operations and all the entire stack to prevent big data structures to be copied.

You should expect a near perfect experience if you meet the client requirements and the network requirements.

##Browser support

We strongly recommend use the spice web client with Chromium/Chrome or Firefox, however it should work at least on:

- Google Chrome
- Firefox
- Internet Explorer 11
- Edge


##How to use it

In order to work you only need to provide the IP address of the websockets proxy and the port
of the websockets proxy.

You can do it permanently editing run.js or through the URL using the parameters:

http://example.com/spice-web-client/index.html?host=IP_ADDRESS_OF_WEBSOCKIFY&port=TCP_PORT_OF_WEBSOCKIFY

By doing this you will connect to the remote spice session and the resolution will be adapted to your browser viewport area.

##Notes For linux sessions
If you are planning to use this to connect to remote linux sessions you should consider disabling compositing on your desktop. The best performance is achieved with
kde with compositing and visual effects disabled.

Always install the spice-vdagent and xorg-qxl to get the best results and to have custom resolutions etc.

##Notes For Windows sessions

Spice web client has a very good performance connecting to remote windows sessions. Always install the spice-agent package including the qxl video driver to get the best results and to have custom resolutions etc.

##More information

For more information about the implementation or questions about roadmap etc contact Jose Carlos Norte (jcarlosn) at jose@eyeos.com

##License

Spice Web Client is distributed under the terms of the [MIT license](https://opensource.org/licenses/MIT).

