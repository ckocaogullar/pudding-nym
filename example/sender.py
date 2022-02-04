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
            "recipient": "DJr5NiZaEa6b1sWT4MRTFEyqkbHxcfQwmgpXuERC8wru.9yHrjyWH6etTjSGMTtwY5CFMKaeGija8nc8nfMjC4Fq3@83x9YyNkQ5QEY84ZU6Wmq8XHqfwf9SUtR7g5PAYB1FRY",
            "withReplySurb": True,
        })
        print("....")
        print(text_send)
        print("....")
        print("sending '{}' (*with* reply SURB) over the mix network...".format(message))
        await websocket.send(text_send)

        print("waiting to receive a message from the mix network...")
        received_message = json.loads(await websocket.recv())
        print("received '{}' from the mix network".format(
            received_message["message"]))


async def ping_wait():
    uri = "ws://localhost:1977"
    async with websockets.connect(uri) as websocket:
        pong_waiter = await websocket.ping()
        await pong_waiter

# asyncio.get_event_loop().run_until_complete(ping_wait())
asyncio.get_event_loop().run_until_complete(send_text_with_surb())
