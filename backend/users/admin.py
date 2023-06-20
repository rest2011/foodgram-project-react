from django.contrib import admin

from .models import Follow, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    empty_value_display = '-пусто-'
    list_display = ('id', 'username', 'email', 'first_name', 'last_name',)
    list_filter = ('first_name', 'email',)
    search_fields = ('username', 'email',)


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    search_fields = ('user', 'author',)
    list_filter = ('author',)
    list_display = ('user', 'author',)
