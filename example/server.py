import asyncio
import websockets
import json

self_address_request = json.dumps({
    "type": "selfAddress"
})


async def reply_text_with_surb():
    uri = "ws://localhost:1978"
    async with websockets.connect(uri) as websocket:
        await websocket.send(self_address_request)
        self_address = json.loads(await websocket.recv())
        print("our address is: {}".format(self_address["address"]))
        
        print("waiting to receive a message from the mix network...")
        received_message = json.loads(await websocket.recv())
        print("received '{}' from the mix network".format(received_message))

        # use the received surb to send an anonymous reply!
        reply_surb = received_message["replySurb"]

        reply_message = "hello from reply SURB!"
        reply = json.dumps({
            "type": "reply",
            "message": reply_message,
            "replySurb": reply_surb
        })

        print("sending '{}' (using reply SURB!) over the mix network...".format(
            reply_message))
        await websocket.send(reply)


asyncio.get_event_loop().run_until_complete(reply_text_with_surb())
