#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-
##  MIT License
##  
##  Copyright (c) 2021 Bash Club
##  
##  Permission is hereby granted, free of charge, to any person obtaining a copy
##  of this software and associated documentation files (the "Software"), to deal
##  in the Software without restriction, including without limitation the rights
##  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
##  copies of the Software, and to permit persons to whom the Software is
##  furnished to do so, subject to the following conditions:
##  
##  The above copyright notice and this permission notice shall be included in all
##  copies or substantial portions of the Software.
##  
##  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
##  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
##  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
##  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
##  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
##  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
##  SOFTWARE.

from cmk.gui.i18n import _
from cmk.gui.plugins.metrics import (
    metric_info,
    graph_info,
    translation
)


# Colors:
#
#                   red
#  magenta                       orange
#            11 12 13 14 15 16
#         46                   21
#         45                   22
#   blue  44                   23  yellow
#         43                   24
#         42                   25
#         41                   26
#            36 35 34 33 32 31
#     cyan                       yellow-green
#                  green
#
# Special colors:
# 51  gray
# 52  brown 1
# 53  brown 2
#
# For a new metric_info you have to choose a color. No more hex-codes are needed!
# Instead you can choose a number of the above color ring and a letter 'a' or 'b
# where 'a' represents the basic color and 'b' is a nuance/shading of the basic color.
# Both number and letter must be declared!
#
# Example:
# "color" : "23/a" (basic color yellow)
# "color" : "23/b" (nuance of color yellow)
#


metric_info["satisfaction"] = {
    "title": _("Satisfaction"),
    "unit": "%",
    "color": "16/a",
}

metric_info["poe_current"] = {
    "title": _("PoE Current"),
    "unit": "a",
    "color": "16/a",
}
metric_info["poe_voltage"] = {
    "title": _("PoE Voltage"),
    "unit": "v",
    "color": "12/a",
}
metric_info["poe_power"] = {
    "title": _("PoE Power"),
    "unit": "w",
    "color": "16/a",
}

metric_info["user_sta"] = {
    "title": _("User"),
    "unit": "",
    "color": "13/b",
}
metric_info["guest_sta"] = {
    "title": _("Guest"),
    "unit": "",
    "color": "13/a",
}

graph_info["user_sta_combined"] = {
    "title" : _("User"),
    "metrics" : [
        ("user_sta","area"),
        ("guest_sta","stack"),
    ],
}

metric_info["lan_user_sta"] = {
    "title": _("LAN User"),
    "unit": "count",
    "color": "13/b",
}
metric_info["lan_guest_sta"] = {
    "title": _("LAN Guest"),
    "unit": "count",
    "color": "13/a",
}

graph_info["lan_user_sta_combined"] = {
    "title" : _("LAN-User"),
    "metrics" : [
        ("lan_user_sta","area"),
        ("lan_guest_sta","stack"),
    ],
}

metric_info["wlan_user_sta"] = {
    "title": _("WLAN User"),
    "unit": "count",
    "color": "13/b",
}
metric_info["wlan_guest_sta"] = {
    "title": _("WLAN Guest"),
    "unit": "count",
    "color": "13/a",
}
metric_info["wlan_iot_sta"] = {
    "title": _("WLAN IoT Devices"),
    "unit": "count",
    "color": "14/a",
}

graph_info["wlan_user_sta_combined"] = {
    "title" : _("WLAN-User"),
    "metrics" : [
        ("wlan_user_sta","area"),
        ("wlan_guest_sta","stack"),
        ("wlan_iot_sta","stack"),
    ],
}

metric_info["wlan_24Ghz_num_user"] = {
    "title": _("User 2.4Ghz"),
    "unit": "count",
    "color": "13/b",
}
metric_info["wlan_5Ghz_num_user"] = {
    "title": _("User 5Ghz"),
    "unit": "count",
    "color": "13/a",
}

graph_info["wlan_user_band_combined"] = {
    "title" : _("WLAN User"),
    "metrics" : [
        ("wlan_24Ghz_num_user","area"),
        ("wlan_5Ghz_num_user","stack"),
    ],
}

#na_avg_client_signal
#ng_avg_client_signal


metric_info["wlan_if_in_octets"] = {
    "title": _("Input Octets"),
    "unit": "bytes/s",
    "color": "#00e060",
}
metric_info["wlan_if_out_octets"] = {
    "title": _("Output Octets"),
    "unit": "bytes/s",
    "color": "#00e060",
}
graph_info["wlan_bandwidth_translated"] = {
    "title": _("Bandwidth WLAN"),
    "metrics": [
        ("wlan_if_in_octets,8,*@bits/s", "area", _("Input bandwidth")),
        ("wlan_if_out_octets,8,*@bits/s", "-area", _("Output bandwidth")),
    ],
    "scalars": [
        ("if_in_octets:warn", _("Warning (In)")),
        ("if_in_octets:crit", _("Critical (In)")),
        ("if_out_octets:warn,-1,*", _("Warning (Out)")),
        ("if_out_octets:crit,-1,*", _("Critical (Out)")),
    ],
}


metric_info["na_avg_client_signal"] = {
    "title" :_("Average Signal 5Ghz"),
    "unit"  : "db",
    "color" : "14/a",
}
metric_info["ng_avg_client_signal"] = {
    "title" :_("Average Signal 2.4Ghz"),
    "unit"  : "db",
    "color" : "#80f000",
}
graph_info["avg_client_signal_combined"] = {
    "title" : _("Average Client Signal"),
    "metrics" : [
        ("na_avg_client_signal","line"),
        ("ng_avg_client_signal","line"),
    ],
    "range" : (-100,0)
}


## different unit ???
#graph_info["poe_usage_combined"] = {
#    "title" : _("PoE Usage"),
#    "metrics" : [
#        ("poe_power","area"),
#        ("poe_voltage","line"),
#    ],
#}

### fixme default uptime translation?
metric_info["unifi_uptime"] = {
    "title" :_("Uptime"),
    "unit"  : "s",
    "color" : "#80f000",
}

check_metrics["check_mk-unifi_network_ports_if"] = translation.if_translation
