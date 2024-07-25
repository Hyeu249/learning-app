/** @odoo-module */

import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component, xml, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
const rpc = require('web.rpc')
const core = require('web.core');

class AudioPlayer extends Component {}

AudioPlayer.template = xml`
    <video controls="" autoplay="" name="media" style="width:100%; height:50px;">
        <source t-att-src="props.value" type="audio/mpeg"/>
    </video>
`;


AudioPlayer.props = {
    ...standardFieldProps,
};
AudioPlayer.supportedTypes = ["char"];

registry.category("fields").add("audio_player", AudioPlayer);

// button widget
class Button extends Component {

    setup() {
        this.state = useState({
            statusClass: "sidebar-button",
        });
    }
    
    togglePlay() {
        const vocabulary = this.props.record.data.translate_version
        this.setStatusClass(vocabulary == this.props.value)
        this.actionSetIsRight(vocabulary == this.props.value)
    }
    
    setStatusClass(isRight){
        this.state.statusClass = isRight ? "sidebar-button success" : "sidebar-button danger"
    }

    async actionSetIsRight(isRight=False){
        try {
            const result = await rpc.query({
                model: 'learning.test',
                method: 'set_is_right',
                args: [this.props.record.data.id, isRight],
            });

        } catch (error) {
            console.log("error: ", error);

        }
    }
}

Button.template = xml`
    <button t-on-click="togglePlay" t-att-class="state.statusClass">
        <t t-esc="props.value"/>
    </button>
`;

Button.props = {
    ...standardFieldProps,
};
Button.supportedTypes = ["char"];

registry.category("fields").add("button", Button);

// progress bar widget
class ProgressBar extends Component {
    
}

ProgressBar.template = xml`
    <div class="progress-container">
        <div class="progress-bar" t-att-style="'width:' + props.value + '%'"></div>
    </div>
`;

ProgressBar.props = {
    ...standardFieldProps,
};
ProgressBar.supportedTypes = ["integer"];

registry.category("fields").add("custom_progressbar", ProgressBar);
