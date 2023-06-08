# consumers.py
from channels.generic.websocket import AsyncWebsocketConsumer
import json

class MeetingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print("connection called")
        # Authenticate and authorize the user
        # Add the user to the meeting group or any other authorization logic

        await self.accept()

    async def disconnect(self, close_code):
        print("disconnected")
        # Clean up any resources related to the user's connection
        pass

    async def receive(self, text_data):
        print("Message received from client",text_data)
        await self.send(text_data=json.dumps({"message": "HEllo"}))
        # Handle received data, such as meeting requests and responses
        pass
