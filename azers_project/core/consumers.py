import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatMessage, Conversation

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        user = self.scope['user']

        # Fetch conversation to check who the artist (receiver) is
        conversation = await self.get_conversation(self.room_id)

        # is_guest = not logged in OR logged in but NOT the artist of this conversation
        is_guest = (not user.is_authenticated) or (user != conversation.receiver)
        sender_id = user.id if not is_guest else None

        await self.save_message(sender_id, self.room_id, message, is_guest)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender_id': sender_id,
                'is_from_guest': is_guest
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender_id': event['sender_id'],
            'is_from_guest': event['is_from_guest']
        }))

    @database_sync_to_async
    def get_conversation(self, room_id):
        return Conversation.objects.select_related('receiver').get(id=room_id)

    @database_sync_to_async
    def save_message(self, user_id, room_id, message, is_guest):
        return ChatMessage.objects.create(
            sender_id=user_id,
            conversation_id=room_id,
            text=message,
            is_from_guest=is_guest
        )


# import json
# from channels.generic.websocket import AsyncWebsocketConsumer
# from channels.db import database_sync_to_async
# from .models import ChatMessage, Conversation

# class ChatConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         self.room_id = self.scope['url_route']['kwargs']['room_id']
#         self.room_group_name = f'chat_{self.room_id}'

#         await self.channel_layer.group_add(self.room_group_name, self.channel_name)
#         await self.accept()

#     async def disconnect(self, close_code):
#         await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

#     async def receive(self, text_data):
#         data = json.loads(text_data)
#         message = data['message']
#         user = self.scope['user']

#         # Check if this is a guest chat room by looking at the conversation
#         conversation = await self.get_conversation(self.room_id)
        
#         # Identify if sender is the authenticated artist or a guest
#         is_guest = not user.is_authenticated
#         sender_id = user.id if not is_guest else None

#         # Save to DB
#         await self.save_message(sender_id, self.room_id, message, is_guest)

#         # Broadcast to room
#         await self.channel_layer.group_send(
#             self.room_group_name,
#             {
#                 'type': 'chat_message',
#                 'message': message,
#                 'sender_id': sender_id,
#                 'is_from_guest': is_guest
#             }
#         )

#     async def chat_message(self, event):
#         await self.send(text_data=json.dumps({
#             'message': event['message'],
#             'sender_id': event['sender_id'],
#             'is_from_guest': event['is_from_guest']
#         }))

#     @database_sync_to_async
#     def save_message(self, user_id, room_id, message, is_guest):
#         return ChatMessage.objects.create(
#             sender_id=user_id,
#             conversation_id=room_id,
#             text=message,
#             is_from_guest=is_guest
#         )