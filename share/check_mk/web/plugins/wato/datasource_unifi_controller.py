#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-

from cmk.gui.i18n import _
from cmk.gui.plugins.wato import (
    HostRulespec,
    IndividualOrStoredPassword,
    rulespec_registry,
)
from cmk.gui.valuespec import (
    Dictionary,
    Alternative,
    NetworkPort,
    Checkbox,
    TextAscii,
)

from cmk.gui.plugins.wato.datasource_programs import RulespecGroupDatasourceProgramsHardware

def _valuespec_special_agent_unifi_controller():
    return Dictionary(
        title = _('Unifi Controller via API'),
        help = _('This rule selects the Unifi API agent'),
        optional_keys=['site'],
        elements=[
            ('user',TextAscii(title = _('API Username.'),allow_empty = False,)),
            ('password',IndividualOrStoredPassword(title = _('API password'),allow_empty = False,)),
            ('site',TextAscii(title = _('Site Name'),allow_empty = False,default_value='default')), ## optional but not empty
            ('port',NetworkPort(title = _('Port'),default_value = 443)),
            ('ignore_cert', Checkbox(title=_("Ignore certificate validation"), default_value=False)),
            ('piggyback', 
                Alternative(
                    title = _('Receive piggyback data by'),
                    elements = [
                        FixedValue("name", title = _("Hostname")),
                        FixedValue("ip", title = _("IP")),
                        FixedValue("none", title = _("None")),
                    ],
                    default_value = "name"
                )
            )
        ]
    )

rulespec_registry.register(
    HostRulespec(
        group=RulespecGroupDatasourceProgramsHardware,
        #IMPORTANT, name must follow special_agents:<name>, 
        #where filename of our special agent located in path local/share/check_mk/agents/special/ is  agent_<name>
        name='special_agents:unifi_controller',
        valuespec=_valuespec_special_agent_unifi_controller,
    ))
