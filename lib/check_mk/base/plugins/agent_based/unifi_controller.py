#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-
#
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

from .agent_based_api.v1 import (
    Metric,
    register,
    render,
    Result,
    IgnoreResults,
    Service,
    State,
    TableRow,
    Attributes
)

from .agent_based_api.v1.type_defs import CheckResult, DiscoveryResult
from typing import Any, Dict, Mapping, Sequence, Optional

from dataclasses import dataclass
from collections import defaultdict
from .utils import interfaces

SubSection = Dict[str,str]
Section = Dict[str, SubSection]
class dictobject(defaultdict):
    def __getattr__(self,name):
        return self[name] if name in self else ""

nested_dictobject = lambda: dictobject(nested_dictobject)

def _expect_bool(val,expected=True,failstate=State.WARN):
    return State.OK if bool(int(val)) == expected else failstate

def _expect_number(val,expected=0,failstate=State.WARN):
    return State.OK if int(val) == expected else failstate

def _safe_float(val):
    try:
        return float(val)
    except (TypeError,ValueError):
        return 0

def _safe_int(val,default=0):
    try:
        return int(val)
    except (TypeError,ValueError):
        return default

def _unifi_status2state(status):
    return {
        "ok"        : State.OK,
        "warning"   : State.WARN,
        "error"     : State.CRIT
    }.get(status.lower(),State.UNKNOWN)

from pprint import pprint

def parse_unifi_dict(string_table):
    _ret = dictobject()
    for _line in string_table:
        _ret[_line[0]] = _line[1]
    return _ret

def parse_unifi_nested_dict(string_table):
    _ret = nested_dictobject()
    for _line in string_table:
        _ret[_line[0]][_line[1]] = _line[2]
    return _ret

UNIFI_DEVICE_STATES = {
    "0" : "disconnected",
    "1" : "connected",
    "2" : "pending"
}


############ Controller ############
def discovery_unifi_controller(section):
    yield Service(item="Unifi Controller")
    if section.cloudkey_version:
        yield Service(item="Cloudkey")

def check_unifi_controller(item,section):
    if item == "Unifi Controller":
        yield Result(
            state=State.OK,
            summary=f"Version: {section.controller_version}"
        )
        if int(section.update_available) > 0:
            yield Result(
                state=State.WARN,
                notice=_("Update available")
            )
    if item == "Cloudkey":
        yield Result(
            state=State.OK,
            summary=f"Version: {section.cloudkey_version}"
        )
        if int(section.cloudkey_update_available) > 0:
            yield Result(
                state=State.WARN,
                notice=_("Update available")
            )

def inventory_unifi_controller(section):
    yield Attributes(
        path=["software","os"],
        inventory_attributes={
            "controller_version" : section.get("controller_version")
        }
    )

register.agent_section(
    name = 'unifi_controller',
    parse_function = parse_unifi_dict
)

register.check_plugin(
    name='unifi_controller',
    service_name='%s',
    discovery_function=discovery_unifi_controller,
    check_function=check_unifi_controller,
)

register.inventory_plugin(
    name = "unifi_controller",
    inventory_function = inventory_unifi_controller
)

############ SITES ###########

def discovery_unifi_sites(section):
    for _item in section.values():
        yield Service(item=f"{_item.desc}")

def check_unifi_sites(item,params,section):
    site = next(filter(lambda x: x.desc == item,section.values()))
    yield Metric("satisfaction",max(0,_safe_int(site.satisfaction)))

    if site.lan_status != "unknown":
        yield Metric("lan_user_sta",_safe_int(site.lan_num_user))
        yield Metric("lan_guest_sta",_safe_int(site.lan_num_guest))
        yield Metric("if_in_octets",_safe_int(site.lan_rx_bytes_r))
        #yield Metric("if_in_bps",_safe_int(site.lan_rx_bytes_r)*8)
        yield Metric("if_out_octets",_safe_int(site.lan_tx_bytes_r))
        #yield Metric("if_out_bps",_safe_int(site.lan_tx_bytes_r)*8)
        yield Metric("lan_active_sw",_safe_int(site.lan_num_sw))
        yield Metric("lan_total_sw",_safe_int(site.lan_num_adopted))
        yield Result(
            state=_unifi_status2state(site.lan_status),
            summary=f"LAN: {site.lan_num_sw}/{site.lan_num_adopted} Switch ({site.lan_status})"
        )
        #yield Result(
        #    state=_expect_number(site.lan_num_disconnected),
        #    notice=f"{site.lan_num_disconnected} Switch disconnected" ##disconnected kann 
        #)

    if site.wlan_status != "unknown":
        yield Metric("wlan_user_sta",_safe_int(site.wlan_num_user))
        yield Metric("wlan_guest_sta",_safe_int(site.wlan_num_guest))
        yield Metric("wlan_iot_sta",_safe_int(site.wlan_num_iot))
        yield Metric("wlan_if_in_octets",_safe_int(site.wlan_rx_bytes_r))
        yield Metric("wlan_if_out_octets",_safe_int(site.wlan_tx_bytes_r))
        yield Metric("wlan_active_ap",_safe_int(site.wlan_num_ap))
        yield Metric("wlan_total_ap",_safe_int(site.wlan_num_adopted))
        yield Result(
            state=_unifi_status2state(site.wlan_status),
            summary=f"WLAN: {site.wlan_num_ap}/{site.wlan_num_adopted} AP ({site.wlan_status})"
        )
        #yield Result(
        #    state=_expect_number(site.wlan_num_disconnected),
        #    notice=f"{site.wlan_num_disconnected} AP disconnected"
        #)
    if site.wan_status != "unknown":
        yield Result(
            state=_unifi_status2state(site.wan_status),
            summary=f"WAN Status: {site.wan_status}"
        )
    if site.www_status != "unknown":
        yield Result(
            state=_unifi_status2state(site.www_status),
            summary=f"WWW Status: {site.www_status}"
        )
    if site.vpn_status != "unknown":
        yield Result(
            state=_unifi_status2state(site.vpn_status),
            notice=f"WWW Status: {site.vpn_status}"
        )

    if params.get("ignore_alarms"):
        _alarmstate = State.OK
    else:
        _alarmstate = _expect_number(site.num_new_alarms)

    yield Result(
        state=_alarmstate,
        notice=f"{site.num_new_alarms} new Alarm"
    )


register.agent_section(
    name = 'unifi_sites',
    parse_function = parse_unifi_nested_dict
)

register.check_plugin(
    name='unifi_sites',
    service_name='Site %s',
    discovery_function=discovery_unifi_sites,
    check_default_parameters={},
    check_ruleset_name="unifi_sites",
    check_function=check_unifi_sites,
)

############ DEVICE_SHORTLIST ##########

def inventory_unifi_device_shortlist(section):
    for _name,_device in section.items():
        yield TableRow(
            path=["hardware","networkdevices"],
            key_columns={"_name"   : _name},
            inventory_columns={
                "serial"     : _device.get("serial"),
                "_state"     : UNIFI_DEVICE_STATES.get(_device.state,"unknown"),
                "vendor"    : "ubiquiti",
                "model"     : _device.get("model_name",_device.get("model")),
                "version"   : _device.version,
                "ip_address": _device.ip,
                "mac"       : _device.mac
            }
        )

register.agent_section(
    name = 'unifi_device_shortlist',
    parse_function = parse_unifi_nested_dict
)

register.inventory_plugin(
    name = "unifi_device_shortlist",
    inventory_function = inventory_unifi_device_shortlist
)



############ DEVICE ###########
def discovery_unifi_device(section):
    yield Service(item="Device Status")
    yield Service(item="Unifi Device")
    yield Service(item="Active-User")
    if  section.type != "uap":  # kein satisfaction bei ap .. radio/ssid haben schon
        yield Service(item="Satisfaction")
    if section.general_temperature:
        yield Service(item="Temperature")
    if section.uplink_device:
        yield Service(item="Uplink")
    if section.speedtest_status:
        yield Service(item="Speedtest")

def check_unifi_device(item,section):
    _device_state = UNIFI_DEVICE_STATES.get(section.state,"unknown")
    ## connected OK / pending Warn / Rest Crit
    _hoststatus = State.OK if section.state == "1" else State.WARN if section.state == "2" else State.CRIT
    if item == "Device Status":
        yield Result(
            state=_hoststatus,
            summary=f"Status: {_device_state}"
        )
    #if section.state != "1":
    #    yield IgnoreResults(f"device not active State: {section.state}")
        
    if item == "Unifi Device":
        yield Result(
            state=State.OK,
            summary=f"Version: {section.version}"
        )
        if _safe_int(section.upgradable) > 0:
            yield Result(
                state=State.WARN,
                notice=_("Update available")
            )
    if item == "Active-User":
        _active_user = _safe_int(section.user_num_sta)
        yield Result(
            state=State.OK,
            summary=f"{_active_user}"
        )
        if _safe_int(section.guest_num_sta) > -1:
            yield Result(
                state=State.OK,
                summary=f"Guest: {section.guest_num_sta}"
            )
        yield Metric("user_sta",_active_user)
        yield Metric("guest_sta",_safe_int(section.guest_num_sta))
    if item == "Satisfaction":
        yield Result(
            state=State.OK,
            summary=f"{section.satisfaction}%"
        )
        yield Metric("satisfaction",max(0,_safe_int(section.satisfaction)))
    if item == "Temperature":
        yield Metric("temp",_safe_float(section.general_temperature))
        yield Result(
            state=State.OK,
            summary=f"{section.general_temperature} °C"
        )
        if section.fan_level:
            yield Result(
                state=State.OK,
                summary=f"Fan: {section.fan_level}%"
            )
    if item == "Speedtest":
        yield Result(
            state=State.OK,
            summary=f"Ping: {section.speedtest_ping} ms"
        )
        yield Result(
            state=State.OK,
            summary=f"Down: {section.speedtest_download} Mbit/s"
        )
        yield Result(
            state=State.OK,
            summary=f"Up: {section.speedtest_upload} Mbit/s"
        )
        _speedtest_time = render.datetime(_safe_float(section.speedtest_time))
        yield Result(
            state=State.OK,
            summary=f"Last: {_speedtest_time}"
        )
        yield Metric("rtt",_safe_float(section.speedtest_ping))
        yield Metric("if_in_bps",_safe_float(section.speedtest_download)*1024*1024) ## mbit to bit
        yield Metric("if_out_bps",_safe_float(section.speedtest_upload)*1024*1024) ## mbit to bit
            
    if item == "Uplink":
        yield Result(
            state=_expect_bool(section.uplink_up),
            summary=f"Device {section.uplink_device} Port: {section.uplink_remote_port}"
        )

def inventory_unifi_device(section):
    yield Attributes(
        path=["software","os"],
        inventory_attributes={
            "version"   : section.get("version")
        }
    )
    yield Attributes(
        path=["software","configuration","snmp_info"],
        inventory_attributes = {
            "name"      : section.get("name"),
            "contact"   : section.get("snmp_contact"),
            "location"  : section.get("snmp_location")
        }
    )
    _hwdict = {
        "vendor"    : "ubiquiti",
    }
    for _key in ("model","board_rev","serial","mac"):
        _val = section.get(_key)
        if _val:
            _hwdict[_key] = _val
    yield Attributes(
        path=["hardware","system"],
        inventory_attributes= _hwdict
    )

register.agent_section(
    name = 'unifi_device',
    parse_function = parse_unifi_dict
)

register.check_plugin(
    name='unifi_device',
    service_name='%s',
    discovery_function=discovery_unifi_device,
    check_function=check_unifi_device,
)

register.inventory_plugin(
    name = "unifi_device",
    inventory_function = inventory_unifi_device
)

############ DEVICEPORT ###########
@dataclass
class unifi_interface(interfaces.InterfaceWithCounters):
    jumbo           : bool = False
    satisfaction    : int = 0
    poe_enable      : bool = False
    poe_mode        : Optional[str] = None
    poe_good        : Optional[bool] = None
    poe_current     : Optional[float] = 0
    poe_power       : Optional[float] = 0
    poe_voltage     : Optional[float] = 0
    poe_class       : Optional[str] = None
    dot1x_mode      : Optional[str] = None
    dot1x_status    : Optional[str] = None
    ip_address      : Optional[str] = None
    portconf        : Optional[str] = None


def _convert_unifi_counters_if(section: Section) -> interfaces.Section:
    ##  10|port_idx|10
    ##  10|port_poe|1
    ##  10|poe_caps|7
    ##  10|op_mode|switch
    ##  10|poe_mode|auto
    ##  10|anomalies|0
    ##  10|autoneg|1
    ##  10|dot1x_mode|unknown
    ##  10|dot1x_status|disabled
    ##  10|enable|1
    ##  10|full_duplex|1
    ##  10|is_uplink|0
    ##  10|jumbo|1
    ##  10|poe_class|Unknown
    ##  10|poe_current|0.00
    ##  10|poe_enable|0
    ##  10|poe_good|0
    ##  10|poe_power|0.00
    ##  10|poe_voltage|0.00
    ##  10|rx_broadcast|1290
    ##  10|rx_bytes|38499976384
    ##  10|rx_dropped|0
    ##  10|rx_errors|0
    ##  10|rx_multicast|16423
    ##  10|rx_packets|125489263
    ##  10|satisfaction|100
    ##  10|satisfaction_reason|0
    ##  10|speed|1000
    ##  10|stp_pathcost|20000
    ##  10|stp_state|forwarding
    ##  10|tx_broadcast|20791854
    ##  10|tx_bytes|238190158091
    ##  10|tx_dropped|0
    ##  10|tx_errors|0
    ##  10|tx_multicast|262691
    ##  10|tx_packets|228482694
    ##  10|tx_bytes_r|17729
    ##  10|rx_bytes_r|176941
    ##  10|bytes_r|194671
    ##  10|name|Port 10
    ##  10|aggregated_by|0
    ##  10|oper_status|1
    ##  10|admin_status|1
    ##  10|portconf|ALL
    ##  unifi_interface(index='10', descr='Port 10', alias='Port 10', type='6', speed=1000000000, oper_status='1', 
    ##      in_octets=38448560321, in_ucast=125404491, in_mcast=16414, in_bcast=1290, in_discards=0, in_errors=0, 
    ##      out_octets=238185160794, out_ucast=228451699, out_mcast=262551, out_bcast=20783341, out_discards=0, out_errors=0, 
    ##      out_qlen=0, phys_address='', oper_status_name='up', speed_as_text='', group=None, node=None, admin_status='1', 
    ##      total_octets=276633721115, jumbo=True, satisfaction=100,
    ##      poe_enable=False, poe_mode='auto', poe_good=None, poe_current=0.0, poe_power=0.0, poe_voltage=0.0, poe_class='Unknown', 
    ##      dot1x_mode='unknown',dot1x_status='disabled', ip_address='', portconf='ALL')

    return [ 
        unifi_interface(
            attributes=interfaces.Attributes(
                index=str(netif.port_idx),
                descr=netif.name,
                alias=netif.name,
                type='6',
                speed=_safe_int(netif.speed)*1000000,
                oper_status=netif.oper_status,
                admin_status=netif.admin_status,
            ),
            counters=interfaces.Counters(
                in_octets=_safe_int(netif.rx_bytes),
                in_ucast=_safe_int(netif.rx_packets),
                in_mcast=_safe_int(netif.rx_multicast),
                in_bcast=_safe_int(netif.rx_broadcast),
                in_disc=_safe_int(netif.rx_dropped),
                in_err=_safe_int(netif.rx_errors),
                out_octets=_safe_int(netif.tx_bytes),
                out_ucast=_safe_int(netif.tx_packets),
                out_mcast=_safe_int(netif.tx_multicast),
                out_bcast=_safe_int(netif.tx_broadcast),
                out_disc=_safe_int(netif.tx_dropped),
                out_err=_safe_int(netif.tx_errors),
            ),
            jumbo=True if netif.jumbo == "1" else False,
            satisfaction=_safe_int(netif.satisfaction) if netif.satisfaction and netif.oper_status == "1" else 0,
            poe_enable=True if netif.poe_enable == "1" else False,
            poe_mode=netif.poe_mode,
            poe_current=float(netif.poe_current) if netif.poe_current else 0,
            poe_voltage=float(netif.poe_voltage) if netif.poe_voltage else 0,
            poe_power=float(netif.poe_power) if netif.poe_power else 0,
            poe_class=netif.poe_class,
            dot1x_mode=netif.dot1x_mode,
            dot1x_status=netif.dot1x_status,
            ip_address=netif.ip,
            portconf=netif.portconf
        ) for netif in parse_unifi_nested_dict(section).values()
    ]
    


def discovery_unifi_network_port_if(  ## fixme parsed_section_name
    params: Sequence[Mapping[str, Any]],
    section: Section,
) -> DiscoveryResult:
    yield from interfaces.discover_interfaces(
        params,
        _convert_unifi_counters_if(section),
    )


def check_unifi_network_port_if(  ##fixme parsed_section_name 
    item: str,
    params: Mapping[str, Any],
    section: Section,
) -> CheckResult:
    _converted_ifs = _convert_unifi_counters_if(section)
    iface = next(filter(lambda x: _safe_int(item,-1) == _safe_int(x.attributes.index) or item == x.attributes.alias,_converted_ifs),None) ## fix Service Discovery appearance alias/descr
    yield from interfaces.check_multiple_interfaces(
        item,
        params,
        _converted_ifs,
    )
    if iface:
        #pprint(iface)
        if iface.portconf:
            yield Result(
                state=State.OK,
                summary=f"Network: {iface.portconf}"
            )
        yield Metric("satisfaction",max(0,iface.satisfaction))
        #pprint(iface)
        if iface.poe_enable:
            yield Result(
                state=State.OK,
            summary=f"PoE: {iface.poe_power}W"
            )
            #yield Metric("poe_current",iface.poe_current)
            yield Metric("poe_power",iface.poe_power)
            yield Metric("poe_voltage",iface.poe_voltage)
        if iface.ip_address:
            yield Result(
                state=State.OK,
                summary=f"IP: {iface.ip_address}"
            )

def inventory_unifi_network_ports(section):
    _total_ethernet_ports = 0
    _available_ethernet_ports = 0
    for _iface in parse_unifi_nested_dict(section).values():
        _total_ethernet_ports +=1
        _available_ethernet_ports +=1 if _iface.oper_status == '2' else 0
        yield TableRow(
            path=["networking","interfaces"],
            key_columns={"index"    : _safe_int(_iface.port_idx)},
            inventory_columns={
                "description"   : _iface.name,
                "alias"         : _iface.name,
                "speed"         : _safe_int(_iface.speed)*1000000,
                "oper_status"   : _safe_int(_iface.oper_status),
                "admin_status"  : _safe_int(_iface.admin_status),
                "available"     : _iface.oper_status == '2',
                "vlans"         : _iface.portconf,
                "port_type"     : 6,
            }
        )
        
    yield Attributes(
        path=["networking"],
        inventory_attributes={
            "available_ethernet_ports"      : _available_ethernet_ports,
            "total_ethernet_ports"          : _total_ethernet_ports,
            "total_interfaces"              : _total_ethernet_ports
        }
    )

register.check_plugin(
    name='unifi_network_ports_if',
    sections=["unifi_network_ports"],
    service_name='Interface %s',
    discovery_ruleset_name="inventory_if_rules",
    discovery_ruleset_type=register.RuleSetType.ALL,
    discovery_default_parameters=dict(interfaces.DISCOVERY_DEFAULT_PARAMETERS),
    discovery_function=discovery_unifi_network_port_if,
    check_ruleset_name="if",
    check_default_parameters=interfaces.CHECK_DEFAULT_PARAMETERS,
    check_function=check_unifi_network_port_if,
)

register.inventory_plugin(
    name = "unifi_network_ports",
    inventory_function = inventory_unifi_network_ports
)

############ DEVICERADIO ###########
def discovery_unifi_radios(section):
    #pprint(section)
    for _radio in section.values():
        if _radio.radio == "ng":
            yield Service(item="2.4Ghz")
        if _radio.radio == "na":
            yield Service(item="5Ghz")

def check_unifi_radios(item,section):
    _item = { "2.4Ghz" : "ng", "5Ghz" : "na" }.get(item)
    radio = next(filter(lambda x: x.radio == _item,section.values()))
    yield Metric("read_data",_safe_int(radio.rx_bytes))
    yield Metric("write_data",_safe_int(radio.tx_bytes))
    yield Metric("satisfaction",max(0,_safe_int(radio.satisfaction)))
    yield Metric("wlan_user_sta",_safe_int(radio.user_num_sta))
    yield Metric("wlan_guest_sta",_safe_int(radio.guest_num_sta))
    yield Metric("wlan_iot_sta",_safe_int(radio.iot_num_sta))

    yield Result(
        state=State.OK,
        summary=f"Channel: {radio.channel}"
    )
    yield Result(
        state=State.OK,
        summary=f"Satisfaction: {radio.satisfaction}"
    )
    yield Result(
        state=State.OK,
        summary=f"User: {radio.num_sta}"
    )
    yield Result(
        state=State.OK,
        summary=f"Guest: {radio.guest_num_sta}"
    )

register.agent_section(
    name = 'unifi_network_radios',
    parse_function = parse_unifi_nested_dict
)

register.check_plugin(
    name='unifi_network_radios',
    service_name='Radio %s',
    discovery_function=discovery_unifi_radios,
    check_function=check_unifi_radios,
)


############ SSIDs ###########
def discovery_unifi_ssids(section):
    for _ssid in section:
        yield Service(item=_ssid)

def check_unifi_ssids(item,section):
    ssid = section.get(item)
    if ssid:
        _channels = ",".join(list(filter(lambda x: _safe_int(x) > 0,[ssid.ng_channel,ssid.na_channel])))
        yield Result(
            state=State.OK,
            summary=f"Channels: {_channels}"
        )
        if (_safe_int(ssid.ng_is_guest) + _safe_int(ssid.na_is_guest)) > 0:
            yield Result(
                state=State.OK,
                summary="Guest"
            )
        _satisfaction = max(0,min(_safe_int(ssid.ng_satisfaction),_safe_int(ssid.na_satisfaction)))
        yield Result(
            state=State.OK,
            summary=f"Satisfaction: {_satisfaction}"
        )
        _num_sta = _safe_int(ssid.na_num_sta) + _safe_int(ssid.ng_num_sta)
        if _num_sta > 0:
            yield Result(
                state=State.OK,
                summary=f"User: {_num_sta}"
            )
        yield Metric("satisfaction",max(0,_satisfaction))
        yield Metric("wlan_24Ghz_num_user",_safe_int(ssid.ng_num_sta) )
        yield Metric("wlan_5Ghz_num_user",_safe_int(ssid.na_num_sta) )
    
        yield Metric("na_avg_client_signal",_safe_int(ssid.na_avg_client_signal))
        yield Metric("ng_avg_client_signal",_safe_int(ssid.ng_avg_client_signal))
        
        yield Metric("na_tcp_packet_loss",_safe_int(ssid.na_tcp_packet_loss))
        yield Metric("ng_tcp_packet_loss",_safe_int(ssid.ng_tcp_packet_loss))
    
        yield Metric("na_wifi_retries",_safe_int(ssid.na_wifi_retries))
        yield Metric("ng_wifi_retries",_safe_int(ssid.ng_wifi_retries))
        yield Metric("na_wifi_latency",_safe_int(ssid.na_wifi_latency))
        yield Metric("ng_wifi_latency",_safe_int(ssid.ng_wifi_latency))
    
    

register.agent_section(
    name = 'unifi_network_ssids',
    parse_function = parse_unifi_nested_dict
)

register.check_plugin(
    name='unifi_network_ssids',
    service_name='SSID: %s',
    discovery_function=discovery_unifi_ssids,
    check_function=check_unifi_ssids,
)


############ SSIDsListController ###########
def discovery_unifi_ssidlist(section):
    #pprint(section)
    for _ssid in section:
        yield Service(item=_ssid)

def check_unifi_ssidlist(item,section):
    ssid = section.get(item)
    if ssid:
        yield Result(
            state=State.OK,
            summary=f"Channels: {ssid.channels}"
        )
        yield Result(
            state=State.OK,
            summary=f"User: {ssid.num_sta}"
        )
        yield Metric("wlan_24Ghz_num_user",_safe_int(ssid.ng_num_sta) )
        yield Metric("wlan_5Ghz_num_user",_safe_int(ssid.na_num_sta) )
        yield Metric("na_avg_client_signal",_safe_int(ssid.na_avg_client_signal))
        yield Metric("ng_avg_client_signal",_safe_int(ssid.ng_avg_client_signal))
        
        yield Metric("na_tcp_packet_loss",_safe_int(ssid.na_tcp_packet_loss))
        yield Metric("ng_tcp_packet_loss",_safe_int(ssid.ng_tcp_packet_loss))
    
        yield Metric("na_wifi_retries",_safe_int(ssid.na_wifi_retries))
        yield Metric("ng_wifi_retries",_safe_int(ssid.ng_wifi_retries))
        yield Metric("na_wifi_latency",_safe_int(ssid.na_wifi_latency))
        yield Metric("ng_wifi_latency",_safe_int(ssid.ng_wifi_latency))

register.agent_section(
    name = 'unifi_ssid_list',
    parse_function = parse_unifi_nested_dict
)

register.check_plugin(
    name='unifi_ssid_list',
    service_name='SSID: %s',
    discovery_function=discovery_unifi_ssidlist,
    check_function=check_unifi_ssidlist,
)




