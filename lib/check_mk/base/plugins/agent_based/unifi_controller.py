#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-
#
from cmk.gui.i18n import _

from .agent_based_api.v1 import (
    Metric,
    register,
    render,
    Result,
    Service,
    State,
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
        yield Metric("uptime",int(section.uptime))
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
############ SITES ###########

def discovery_unifi_sites(section):
    for _item in section.values():
        yield Service(item=f"{_item.desc}")

def check_unifi_sites(item,section):
    site = next(filter(lambda x: x.desc == item,section.values()))
    yield Metric("satisfaction",max(0,interfaces.saveint(site.satisfaction)))

    if site.lan_status != "unknown":
        yield Metric("lan_user_sta",interfaces.saveint(site.lan_num_user))
        yield Metric("lan_guest_sta",interfaces.saveint(site.lan_num_guest))
        yield Metric("if_in_octets",interfaces.saveint(site.lan_rx_bytes_r))
        #yield Metric("if_in_bps",interfaces.saveint(site.lan_rx_bytes_r)*8)
        yield Metric("if_out_octets",interfaces.saveint(site.lan_tx_bytes_r))
        #yield Metric("if_out_bps",interfaces.saveint(site.lan_tx_bytes_r)*8)
        
        yield Result(
            state=_unifi_status2state(site.lan_status),
            summary=f"LAN: {site.lan_num_sw}/{site.lan_num_adopted} Switch ({site.lan_status})"
        )
        #yield Result(
        #    state=_expect_number(site.lan_num_disconnected),
        #    notice=f"{site.lan_num_disconnected} Switch disconnected" ##disconnected kann 
        #)

    if site.wlan_status != "unknown":
        yield Metric("wlan_user_sta",interfaces.saveint(site.wlan_num_user))
        yield Metric("wlan_guest_sta",interfaces.saveint(site.wlan_num_guest))
        yield Metric("wlan_iot_sta",interfaces.saveint(site.wlan_num_iot))
        yield Metric("wlan_if_in_octets",interfaces.saveint(site.wlan_rx_bytes_r))
        yield Metric("wlan_if_out_octets",interfaces.saveint(site.wlan_tx_bytes_r))
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
    yield Result(
        state=_expect_number(site.num_new_alarms),
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
    check_function=check_unifi_sites,
)

############ DEVICE ###########
def discovery_unifi_device(section):
    yield Service(item="Unifi Device")
    yield Service(item="Uptime")
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
    if item == "Unifi Device":
        yield Result(
            state=State.OK,
            summary=f"Version: {section.version}"
        )
        if interfaces.saveint(section.upgradable) > 0:
            yield Result(
                state=State.WARN,
                notice=_("Update available")
            )
    if item == "Active-User":
        _active_user = interfaces.saveint(section.user_num_sta)
        yield Result(
            state=State.OK,
            summary=f"{_active_user}"
        )
        if interfaces.saveint(section.guest_num_sta) > -1:
            yield Result(
                state=State.OK,
                summary=f"Guest: {section.guest_num_sta}"
            )
        yield Metric("user_sta",_active_user)
        yield Metric("guest_sta",interfaces.saveint(section.guest_num_sta))
    if item == "Uptime":
        _uptime = int(section.uptime) if section.uptime else -1
        if _uptime > 0:
            yield Result(
                state=State.OK,
                summary=render.timespan(_uptime)
            )
            yield Metric("unifi_uptime",_uptime)
    if item == "Satisfaction":
        yield Result(
            state=State.OK,
            summary=f"{section.satisfaction}%"
        )
        yield Metric("satisfaction",max(0,interfaces.saveint(section.satisfaction)))
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
############ DEVICEPORT ###########
@dataclass
class unifi_interface(interfaces.Interface):
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

    def __post_init__(self) -> None:
        self.finalize()

def _convert_unifi_counters_if(section: Section) -> interfaces.Section:
    return [ 
        unifi_interface(
            index=str(netif.port_idx),
            descr=netif.name,
            alias=netif.name,
            type='6',
            speed=interfaces.saveint(netif.speed)*1000000,
            oper_status=netif.oper_status,
            admin_status=netif.admin_status,
            in_octets=interfaces.saveint(netif.rx_bytes),
            in_ucast=interfaces.saveint(netif.rx_packets),
            in_mcast=interfaces.saveint(netif.rx_multicast),
            in_bcast=interfaces.saveint(netif.rx_broadcast),
            in_discards=interfaces.saveint(netif.rx_dropped),
            in_errors=interfaces.saveint(netif.rx_errors),
            out_octets=interfaces.saveint(netif.tx_bytes),
            out_ucast=interfaces.saveint(netif.tx_packets),
            out_mcast=interfaces.saveint(netif.tx_multicast),
            out_bcast=interfaces.saveint(netif.tx_broadcast),
            out_discards=interfaces.saveint(netif.tx_dropped),
            out_errors=interfaces.saveint(netif.tx_errors),
            jumbo=True if netif.jumbo == "1" else False,
            satisfaction=interfaces.saveint(netif.satisfaction) if netif.satisfaction and netif.oper_status == "1" else 0,
            poe_enable=True if netif.poe_enable == "1" else False,
            poe_mode=netif.poe_mode,
            poe_current=float(netif.poe_current) if netif.poe_current else 0,
            poe_voltage=float(netif.poe_voltage) if netif.poe_voltage else 0,
            poe_power=float(netif.poe_power) if netif.poe_power else 0,
            poe_class=netif.poe_class,
            dot1x_mode=netif.dot1x_mode,
            dot1x_status=netif.dot1x_status,
            ip_address=netif.ip
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
    iface = next(filter(lambda x: item in (x.index,x.alias),_converted_ifs),None) ## fix Service Discovery appearance alias/descr
    yield from interfaces.check_multiple_interfaces(
        item,
        params,
        _converted_ifs,
    )
    if iface:
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
    yield Metric("read_data",interfaces.saveint(radio.rx_bytes))
    yield Metric("write_data",interfaces.saveint(radio.tx_bytes))
    yield Metric("satisfaction",max(0,interfaces.saveint(radio.satisfaction)))
    yield Metric("wlan_user_sta",interfaces.saveint(radio.user_num_sta))
    yield Metric("wlan_guest_sta",interfaces.saveint(radio.guest_num_sta))
    yield Metric("wlan_iot_sta",interfaces.saveint(radio.iot_num_sta))

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
    _channels = ",".join(list(filter(lambda x: interfaces.saveint(x) > 0,[ssid.ng_channel,ssid.na_channel])))
    yield Result(
        state=State.OK,
        summary=f"Channels: {_channels}"
    )
    if (interfaces.saveint(ssid.ng_is_guest) + interfaces.saveint(ssid.na_is_guest)) > 0:
        yield Result(
            state=State.OK,
            summary="Guest"
        )
    _satisfaction = max(0,min(interfaces.saveint(ssid.ng_satisfaction),interfaces.saveint(ssid.na_satisfaction)))
    yield Result(
        state=State.OK,
        summary=f"Satisfaction: {_satisfaction}"
    )
    _num_sta = interfaces.saveint(ssid.na_num_sta) + interfaces.saveint(ssid.ng_num_sta)
    if _num_sta > 0:
        yield Result(
            state=State.OK,
            summary=f"User: {_num_sta}"
        )
    yield Metric("satisfaction",max(0,_satisfaction))
    yield Metric("wlan_24Ghz_num_user",interfaces.saveint(ssid.ng_num_sta) )
    yield Metric("wlan_5Ghz_num_user",interfaces.saveint(ssid.na_num_sta) )

    yield Metric("na_avg_client_signal",interfaces.saveint(ssid.na_avg_client_signal))
    yield Metric("ng_avg_client_signal",interfaces.saveint(ssid.ng_avg_client_signal))
    
    yield Metric("na_tcp_packet_loss",interfaces.saveint(ssid.na_tcp_packet_loss))
    yield Metric("ng_tcp_packet_loss",interfaces.saveint(ssid.ng_tcp_packet_loss))

    yield Metric("na_wifi_retries",interfaces.saveint(ssid.na_wifi_retries))
    yield Metric("ng_wifi_retries",interfaces.saveint(ssid.ng_wifi_retries))
    yield Metric("na_wifi_latency",interfaces.saveint(ssid.na_wifi_latency))
    yield Metric("ng_wifi_latency",interfaces.saveint(ssid.ng_wifi_latency))
    
    

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
    yield Result(
        state=State.OK,
        summary=f"Channels: {ssid.channels}"
    )
#    if (interfaces.saveint(ssid.ng_is_guest) + interfaces.saveint(ssid.na_is_guest)) > 0:
#        yield Result(
#            state=State.OK,
#            summary="Guest"
#        )
#    yield Result(
#        state=State.OK,
#        summary=f"Satisfaction: {_satisfaction}"
#    )
    yield Result(
        state=State.OK,
        summary=f"User: {ssid.num_sta}"
    )

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


