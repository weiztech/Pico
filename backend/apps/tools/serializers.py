from rest_framework import serializers
from .models import Tool, UserTool, ToolCategory


class ToolCategorySerializer(serializers.ModelSerializer):
    """Serializer for tool categories."""
    
    tool_count = serializers.ReadOnlyField()
    
    class Meta:
        model = ToolCategory
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class ToolSerializer(serializers.ModelSerializer):
    """Serializer for tools."""
    
    user_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Tool
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class UserToolSerializer(serializers.ModelSerializer):
    """Serializer for user tools."""
    
    tool_name = serializers.CharField(source='tool.name', read_only=True)
    tool_description = serializers.CharField(source='tool.description', read_only=True)
    tool_category = serializers.CharField(source='tool.category', read_only=True)
    connection_string = serializers.ReadOnlyField()
    
    class Meta:
        model = UserTool
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at', 'last_used', 'usage_count')
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class UserToolDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for user tools with full tool information."""
    
    tool = ToolSerializer(read_only=True)
    connection_string = serializers.ReadOnlyField()
    
    class Meta:
        model = UserTool
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at', 'last_used', 'usage_count')


class UserToolCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating user tools."""
    
    class Meta:
        model = UserTool
        fields = ('tool', 'display_name', 'host_name', 'port', 'secret_key', 'extra_config')
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
    
    def validate(self, data):
        tool = data.get('tool')
        user = self.context['request'].user
        
        # Check if user already has this tool configured
        if UserTool.objects.filter(user=user, tool=tool).exists():
            raise serializers.ValidationError(
                f"You already have {tool.name} configured."
            )
        
        # Validate required fields based on tool requirements
        if tool.requires_host and not data.get('host_name'):
            raise serializers.ValidationError(
                f"{tool.name} requires a host name to be configured."
            )
        
        if tool.requires_api_key and not data.get('secret_key'):
            raise serializers.ValidationError(
                f"{tool.name} requires an API key to be configured."
            )
        
        return data


class UserToolUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user tools."""
    
    class Meta:
        model = UserTool
        fields = ('display_name', 'is_active', 'host_name', 'port', 'secret_key', 'extra_config')
    
    def validate(self, data):
        tool = self.instance.tool
        
        # Validate required fields based on tool requirements
        if tool.requires_host:
            host_name = data.get('host_name', self.instance.host_name)
            if not host_name:
                raise serializers.ValidationError(
                    f"{tool.name} requires a host name to be configured."
                )
        
        if tool.requires_api_key:
            secret_key = data.get('secret_key', self.instance.secret_key)
            if not secret_key:
                raise serializers.ValidationError(
                    f"{tool.name} requires an API key to be configured."
                )
        
        return data
