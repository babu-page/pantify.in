"""
Serializers for Order creation API.
"""
from rest_framework import serializers

from .models import Customer, Order, OrderItem


class CustomerSerializer(serializers.ModelSerializer):
    """Customer data for order creation."""

    class Meta:
        model = Customer
        fields = ['name', 'address', 'gstin', 'phone', 'email', 'state_code']
        extra_kwargs = {
            'address': {'required': False, 'allow_blank': True},
            'gstin': {'required': False, 'allow_blank': True},
            'phone': {'required': False, 'allow_blank': True},
            'email': {'required': False, 'allow_blank': True},
            'state_code': {'required': False, 'allow_blank': True},
        }


class OrderItemSerializer(serializers.ModelSerializer):
    """Line item for order creation."""

    hsn_sac = serializers.CharField(default='998313', required=False)

    class Meta:
        model = OrderItem
        fields = ['sno', 'description', 'hsn_sac', 'quantity', 'rate', 'amount']


class OrderCreateSerializer(serializers.Serializer):
    """Create order with customer and items."""

    customer = CustomerSerializer()
    items = OrderItemSerializer(many=True)

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("At least one item is required.")
        return value

    def create(self, validated_data):
        customer_data = validated_data.pop('customer')
        items_data = validated_data.pop('items')

        customer = Customer.objects.create(**customer_data)

        order = Order.objects.create(customer=customer)

        for i, item_data in enumerate(items_data, start=1):
            data = dict(item_data)
            data['sno'] = data.get('sno', i)
            OrderItem.objects.create(order=order, **data)

        return order
