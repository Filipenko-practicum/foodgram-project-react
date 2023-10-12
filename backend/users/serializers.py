from rest_framework import serializers

from .models import User

class UserSerializer(serializers.ModelSerializer):
    """Сериалайзер Юзера."""
    is_subscribed = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model=User
        fields= (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        user=self.context.get('request').user
        return bool(
            user.is_authenticated
            and obj.subscribing.filter(user=user).exists()
        )
