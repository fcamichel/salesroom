import json
from django.contrib.auth.models import User
from django.db import models
from django.utils.six import python_2_unicode_compatible
from channels import Group

from .settings import MSG_TYPE_MESSAGE, MSG_TYPE_COUNT


class BaseMixIn(models.Model):
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        abstract = True


class Product(BaseMixIn):
    title = models.CharField(
        max_length=255
    )
    notes = models.TextField(
        blank=True, null=True
    )
    count = models.FloatField()

    def __str__(self):
        return '%s | %s' % (self.title, self.count)


@python_2_unicode_compatible
class Date(BaseMixIn):
    title = models.CharField(
        max_length=255
    )
    date = models.DateField()
    products = models.ManyToManyField(
        Product
    )

    def __str__(self):
        return '%s | %s' % (self.title, self.date)

    @property
    def websocket_group(self):
        """
        Returns the Channels Group that sockets should subscribe to to get sent
        messages as they are generated.
        """
        return Group("room-%s" % self.id)

    def send_message(self, message, user, msg_type=MSG_TYPE_MESSAGE):
        """
        Called to send a message to the room on behalf of a user.
        """
        final_msg = {'room': str(self.id), 'message': message, 'username': user.username, 'msg_type': msg_type}

        if msg_type == MSG_TYPE_COUNT:
            date = Date.objects.get(pk=self.id)
            product = Product.objects.get(pk=message)
            obj = Activity(date=date, product=product, member=user, count_change=-1.0)
            obj.save()
            final_msg = {
                'room': str(self.id),
                'message': [obj.id, obj.product.title, str(obj.count_change), obj.created_at.strftime("%d.%m.%y %H:%M:%S")],
                'username': user.username,
                'msg_type': MSG_TYPE_MESSAGE
            }

        # Send out the message to everyone in the room
        self.websocket_group.send(
            {"text": json.dumps(final_msg)}
        )


class Activity(BaseMixIn):
    date = models.ForeignKey(
        Date
    )
    product = models.ForeignKey(
        Product
    )
    member = models.ForeignKey(
        User
    )
    count_change = models.FloatField()
