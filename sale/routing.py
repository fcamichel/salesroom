from channels import route
from .consumers import ws_connect, ws_receive, ws_disconnect, sale_join, sale_leave, sale_send


# There's no path matching on these routes; we just rely on the matching
# from the top-level routing. We _could_ path match here if we wanted.
websocket_routing = [
    # Called when WebSockets connect
    route("websocket.connect", ws_connect),

    # Called when WebSockets get sent a data frame
    route("websocket.receive", ws_receive),

    # Called when WebSockets disconnect
    route("websocket.disconnect", ws_disconnect),
]


# You can have as many lists here as you like, and choose any name.
# Just refer to the individual names in the include() function.
custom_routing = [
    # Handling different chat commands (websocket.receive is decoded and put
    # onto this channel) - routed on the "command" attribute of the decoded
    # message.
    route("sale.receive", sale_join, command="^join$"),
    route("sale.receive", sale_leave, command="^leave$"),
    route("sale.receive", sale_send, command="^send$"),
]
