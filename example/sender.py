import asyncio
import json
import websockets

self_address_request = json.dumps({
    "type": "selfAddress"
})


async def send_text_with_surb():
    message = "Hello Nym!"

    uri = "ws://localhost:1977"
    async with websockets.connect(uri) as websocket:
        await websocket.send(self_address_request)
        self_address = json.loads(await websocket.recv())
        print("our address is: {}".format(self_address["address"]))

        text_send = json.dumps({
            "type": "send",
            "message": message,
            "recipient": "HTgnSgopF9UDimUR9KDuqJKMPrAsDEvQoxuzEkJsuw5i.GszykGMXfpEy7hmWhU77JT3yxcbyQ1barRbn5V3xFLiy@CbxxDmmNCufXSsi7hqUnorchtsqqSLSZp7QfRJ5ugSRA",
            "withReplySurb": True,
        })
        print("....")
        print(text_send)
        print("....")
        print("Sending '{}' (*with* reply SURB) over the mix network...".format(message))
        await websocket.send(text_send)
        for i in range(2):
            print("Waiting to receive a message from the mix network...")
            received_message = json.loads(await websocket.recv())
            print("Received '{}' from the mix network".format(
                received_message["message"]))


async def ping_wait():
    uri = "ws://localhost:1977"
    async with websockets.connect(uri) as websocket:
        pong_waiter = await websocket.ping()
        await pong_waiter

# asyncio.get_event_loop().run_until_complete(ping_wait())
asyncio.get_event_loop().run_until_complete(send_text_with_surb())
