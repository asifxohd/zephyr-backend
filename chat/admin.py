from django.contrib import admin
from .models import Conversation, Message,OnlineChatStatus
from .models import DELIVERED, READ  

class ConversationAdmin(admin.ModelAdmin):
    list_display = ('user_one', 'user_two', 'last_updated', 'created_at')  
    search_fields = ('user_one__username', 'user_two__username')  
    list_filter = ('last_updated', 'created_at') 
    ordering = ('-created_at',)

class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'conversation', 'content_type', 'status', 'timestamp') 
    list_filter = ('content_type', 'status', 'timestamp')  
    search_fields = ('sender__username', 'conversation__user_one__username', 'conversation__user_two__username')  
    ordering = ('-timestamp',)  
    actions = ['mark_as_delivered', 'mark_as_read'] 

    def mark_as_delivered(self, request, queryset):
        queryset.update(status=DELIVERED)
        self.message_action_feedback(queryset, 'delivered')

    def mark_as_read(self, request, queryset):
        queryset.update(status=READ)
        self.message_action_feedback(queryset, 'read')

    def message_action_feedback(self, queryset, status):
        count = queryset.count()
        self.message_action_status = f'{count} messages marked as {status}'
        self.message_action_status = ''

    mark_as_delivered.short_description = 'Mark selected messages as Delivered'
    mark_as_read.short_description = 'Mark selected messages as Read'


admin.site.register(Conversation, ConversationAdmin)
admin.site.register(Message, MessageAdmin)
admin.site.register(OnlineChatStatus)
