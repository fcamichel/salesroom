import json
from channels import Channel
from channels.auth import channel_session_user_from_http, channel_session_user
from django.db.models import Sum

from .settings import MSG_TYPE_LEAVE, MSG_TYPE_ENTER, NOTIFY_USERS_ON_ENTER_OR_LEAVE_ROOMS
from .models import Date, Activity, Product
from .utils import get_date_or_error, catch_client_error
from .exceptions import ClientError


### WebSocket handling ###


# This decorator copies the user from the HTTP session (only available in
# websocket.connect or http.request messages) to the channel session (available
# in all consumers with the same reply_channel, so all three here)
@channel_session_user_from_http
def ws_connect(message):
    # Initialise their session
    message.channel_session['dates'] = []


# Unpacks the JSON in the received WebSocket frame and puts it onto a channel
# of its own with a few attributes extra so we can route it
# This doesn't need @channel_session_user as the next consumer will have that,
# and we preserve message.reply_channel (which that's based on)
def ws_receive(message):
    # All WebSocket frames have either a text or binary payload; we decode the
    # text part here assuming it's JSON.
    # You could easily build up a basic framework that did this encoding/decoding
    # for you as well as handling common errors.
    payload = json.loads(message['text'])
    payload['reply_channel'] = message.content['reply_channel']
    Channel("sale.receive").send(payload)


@channel_session_user
def ws_disconnect(message):
    # Unsubscribe from any connected rooms
    for date_id in message.channel_session.get("dates", set()):
        try:
            date = Date.objects.get(pk=date_id)
            # Removes us from the room's send group. If this doesn't get run,
            # we'll get removed once our first reply message expires.
            date.websocket_group.discard(message.reply_channel)
        except Date.DoesNotExist:
            pass


### Sale channel handling ###


# Channel_session_user loads the user out from the channel session and presents
# it as message.user. There's also a http_session_user if you want to do this on
# a low-level HTTP handler, or just channel_session if all you want is the
# message.channel_session object without the auth fetching overhead.
@channel_session_user
@catch_client_error
def sale_join(message):
    # Find the room they requested (by ID) and add ourselves to the send group
    # Note that, because of channel_session_user, we have a message.user
    # object that works just like request.user would. Security!
    date = get_date_or_error(message["room"], message.user)

    # Send a "enter message" to the room if available
    if NOTIFY_USERS_ON_ENTER_OR_LEAVE_ROOMS:
        date.send_message(None, message.user, MSG_TYPE_ENTER)

    # OK, add them in. The websocket_group is what we'll send messages
    # to so that everyone in the sale room gets them.
    date.websocket_group.add(message.reply_channel)
    message.channel_session['dates'] = list(set(message.channel_session['dates']).union([date.id]))
    # Send a message back that will prompt them to open the room
    # Done server-side so that we could, for example, make people
    # join rooms automatically.
    message.reply_channel.send({
        "text": json.dumps({
            "join": str(date.id),
            "title": date.title,
        }),
    })
    activities = Activity.objects.filter(date__pk=message["room"])
    for activity in activities:
        date.send_message(
            [
                activity.id,
                activity.product.title,
                activity.product.id,
                str(activity.count_change),
                activity.created_at.strftime("%d.%m.%y %H:%M:%S")
            ],
            activity.member)

    products = Product.objects.filter(date__id=message["room"])
    for product in products:
        count_calculation = Activity.objects.filter(
            date__pk=message["room"], product=product).aggregate(Sum('count_change'))
        if count_calculation["count_change__sum"] is not None:
            date.send_message(
                [
                    product.title,
                    product.count + count_calculation["count_change__sum"],
                    product.id
                ],
                message.user,
                6
            )
        else:
            date.send_message(
                [
                    product.title,
                    product.count,
                    product.id
                ],
                message.user,
                6
            )



@channel_session_user
@catch_client_error
def sale_leave(message):
    # Reverse of join - remove them from everything.
    date = get_date_or_error(message["room"], message.user)

    # Send a "leave message" to the room if available
    if NOTIFY_USERS_ON_ENTER_OR_LEAVE_ROOMS:
        date.send_message(None, message.user, MSG_TYPE_LEAVE)

    date.websocket_group.discard(message.reply_channel)
    message.channel_session['dates'] = list(set(message.channel_session['dates']).difference([date.id]))
    # Send a message back that will prompt them to close the room
    message.reply_channel.send({
        "text": json.dumps({
            "leave": str(date.id),
        }),
    })


@channel_session_user
@catch_client_error
def sale_send(message):
    # Check that the user in the room
    if int(message['room']) not in message.channel_session['dates']:
        raise ClientError("ROOM_ACCESS_DENIED")
    # Find the room they're sending to, check perms
    date = get_date_or_error(message["room"], message.user)
    # Send the message along
    try:
        date.send_message(message["message"], message.user, message["msg_type"])
    except KeyError:
        date.send_message(message["message"], message.user)
