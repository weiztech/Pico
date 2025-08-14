# chat/consumers.py
import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync

from accounts.models import User
from lit_reviews.models import ArticleReview
from lit_reviews.api.articles.serializers import ArticleReviewSerializer
from lit_reviews.api.home.serializers import UserSerialzer

class LiteratureReviewConsumer(WebsocketConsumer):
    def connect(self):
        print(self.scope["url_route"]["kwargs"]["room_name"])
        self.accept()
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"group_{self.room_name}"

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name, self.channel_name
        )

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name, self.channel_name
        )

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        user_id = self.scope["user"].id
        user = User.objects.get(id=user_id)
        user_ser = UserSerialzer(user)
        
        message["user"] = user_ser.data
        type = text_data_json["type"]

        # self.send(text_data=json.dumps({"message": message}))
        # Send message to room group
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name, {"type": type, "message": message}
        )

    # Receive message from room group
    def review_user_active(self, event):
        message = event["message"]

        # Send message to WebSocket
        self.send(text_data=json.dumps({"message": message, "type": "debug"}))

    def review_state_updated(self, event):
        message = event["message"]
        review_id = message["review_id"]
        review = ArticleReview.objects.get(id=review_id)
        review_ser = ArticleReviewSerializer(review)
        message["review"] = review_ser.data 
        
        # Send message to WebSocket
        self.send(text_data=json.dumps({"message": message, "type": "review_state_updated"}))

    def review_kw_updated(self, event):
        message = event["message"]

        # Send message to WebSocket
        self.send(text_data=json.dumps({"message": message, "type": "review_kw_updated"}))

    def review_second_pass_ai_fields_completed(self, event):
        message = event["message"]

        # Send message to WebSocket
        self.send(text_data=json.dumps({"message": message, "type": "review_second_pass_ai_fields_completed"}))


    def article_review_ai_suggestions_completed(self, event):
        message = event["message"]

        # Send message to WebSocket
        self.send(text_data=json.dumps({"message": message, "type": "article_review_ai_suggestions_completed"}))


    def article_review_ai_suggestions_completed_all(self, event):
        message = event["message"]

        # Send message to WebSocket
        self.send(text_data=json.dumps({"message": message, "type": "article_review_ai_suggestions_completed_all"}))


    def pdf_kw_highlighting_completed(self, event):
        message = event["message"]

        # Send message to WebSocket
        self.send(text_data=json.dumps({
            "message": message, 
            "type": "pdf_kw_highlighting_completed",
        }))


class UserConsumer(WebsocketConsumer):
    def connect(self):
        print(self.scope["url_route"]["kwargs"]["room_name"])
        self.accept()
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"group_{self.room_name}"

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name, self.channel_name
        )

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name, self.channel_name
        )

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        user_id = self.scope["user"].id
        user = User.objects.get(id=user_id)
        user_ser = UserSerialzer(user)
        
        message["user"] = user_ser.data
        type = text_data_json["type"]

        # self.send(text_data=json.dumps({"message": message}))
        # Send message to room group
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name, {"type": type, "message": message}
        )

    # Literature Review Created Successfully
    def literature_review_created(self, event):
        message = event["message"]

        # Send message to WebSocket
        self.send(text_data=json.dumps({"message": message, "type": "debug"}))
