import logging
logging.basicConfig(level=logging.INFO)

from time import sleep, time
from datetime import datetime
import pathlib

import asyncio
import json
import logging
import os
import uuid
import ssl

import cv2

from aiohttp import web
from av import VideoFrame

from aiortc import MediaStreamTrack, RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaBlackhole, MediaPlayer, MediaRecorder

ROOT = os.path.dirname(__file__)
current_dir = str(pathlib.Path(__file__).parent.absolute())

class MainApplication:
    def __init__(self):
        self.user_name = ''

        self.logger = logging.getLogger("pc")
        self.pcs = set()

    async def index(self, request):
        content = open(os.path.join(ROOT, "index.html"), "r").read()

        return web.Response(content_type="text/html", text=content)

    async def javascript(self, request):
    # def javascript(self, request):
        content = open(os.path.join(ROOT, "client.js"), "r").read()
        return web.Response(content_type="application/javascript", text=content)


    async def offer(self, request):
        params = await request.json()
        offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

        self.user_name = params["user_id"]

        pc = RTCPeerConnection()
        pc_id = "PeerConnection(%s)" % uuid.uuid4()
        self.pcs.add(pc)

        def log_info(msg, *args):
            self.logger.info(pc_id + " " + msg, *args)

        log_info("Created for %s", request.remote)

        if not pathlib.Path(current_dir+'/videos/').is_dir():
            pathlib.Path(current_dir+'/videos/').mkdir(parents=True, exist_ok=True) # создание папки для записи видео

        recorder = MediaRecorder(current_dir+'/videos/'+self.user_name+' '+datetime.today().strftime('%Y-%m-%d')+'_'+str(time())+'.mp4')

        @pc.on("datachannel")
        def on_datachannel(channel):
            @channel.on("message")
            def on_message(message):
                if isinstance(message, str) and message.startswith("ping"):
                    channel.send("pong" + message[4:])

        @pc.on("iceconnectionstatechange")
        async def on_iceconnectionstatechange():
            log_info("ICE connection state is %s", pc.iceConnectionState)
            if pc.iceConnectionState == "failed":
                await pc.close()
                self.pcs.discard(pc)

        @pc.on("track")
        def on_track(track):
            log_info("Track %s received", track.kind)

            recorder.addTrack(track)

            if track.kind == "video":
                pc.addTrack(track)

            @track.on("ended")
            async def on_ended():
                log_info("Track %s ended", track.kind)
                track.stop()
                await recorder.stop()

        # handle offer
        await pc.setRemoteDescription(offer)
        await recorder.start()

        # send answer
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)

        return web.Response(
            content_type="application/json",
            text=json.dumps(
                {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
            ),
        )


    async def on_shutdown(self, app):
        # close peer connections
        coros = [pc.close() for pc in self.pcs]
        await asyncio.gather(*coros)
        self.pcs.clear()


if __name__ == "__main__": 
    PORT = 9084
    HOST = '0.0.0.0'
    # ssl_context = None

    ssl_context = ssl.SSLContext()
    ssl_context.load_cert_chain('example.crt', 'example.key')

    logging.info('start')
    app = web.Application()

    main_app = MainApplication()
    logging.info('init_funcs')

    app.on_shutdown.append(main_app.on_shutdown)
    app.router.add_get("/", main_app.index)
    app.router.add_get("/get", main_app.index)
    app.router.add_get("/client.js", main_app.javascript)
    app.router.add_post("/offer", main_app.offer)
    web.run_app(app, access_log=None, host=HOST, port=PORT, ssl_context=ssl_context)

