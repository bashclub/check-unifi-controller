from cmk.gui.plugins.metrics import perfometer_info

perfometer_info.append({
    "type": "linear",
    "segments": ["satisfaction"],
    "total": 100.0,
})

perfometer_info.append({
    "type": "logarithmic",
    "metric": "unifi_uptime",
    "half_value": 2592000.0,
    "exponent": 2,
})

