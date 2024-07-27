/** @odoo-module */

import { standardFieldProps } from "@web/views/fields/standard_field_props"
import {
    Component,
    xml,
    useState,
    onWillUpdateProps,
    onMounted,
    useRef,
} from "@odoo/owl"
import { registry } from "@web/core/registry"
import { useService } from "@web/core/utils/hooks"

class AudioPlayer extends Component {
    audioEl = useRef("audio_widget")
    sourceEl = useRef("source_widget")
    setup() {
        onWillUpdateProps(this.onWillUpdateProps)
    }

    async onWillUpdateProps(nextProps) {
        const nextValue = nextProps.value
        if (nextValue !== this.props.value) {
            this.loadAudio(nextValue)
        }
    }

    loadAudio(src) {
        this.sourceEl.el.setAttribute("src", src)
        this.audioEl.el.load()
    }
}

AudioPlayer.template = xml`
    <audio t-ref="audio_widget" controls="" autoplay="" name="media" style="width:100%; height:50px;">
        <source t-ref="source_widget" t-att-src="props.value" type="audio/mpeg"/>
    </audio>
`

AudioPlayer.props = {
    ...standardFieldProps,
}
AudioPlayer.supportedTypes = ["char"]

registry.category("fields").add("audio_player", AudioPlayer)

// button widget
class AnswerButton extends Component {
    setup() {
        ;(this.res_id = this.props.record.data.id),
            (this.model_name = this.props.record.resModel),
            (this.orm = useService("orm"))
        this.action = useService("action")
    }

    onAction() {
        const vocabulary = this.props.record.data.translate_version
        this.actionSetIsCompleted(vocabulary == this.props.value)
    }

    async actionSetIsCompleted(isCompleted = false) {
        try {
            await this.orm.call(
                this.model_name,
                "set_is_completed",
                [this.res_id, isCompleted],
                {}
            )
            await this.props.record.model.root.load()
            await this.props.record.model.notify()
            this.setStatusClass(isCompleted)
        } catch (error) {
            console.log("actionSetIsCompleted error: ", error)
        }
    }

    setStatusClass(isCompleted) {
        const elements = document.querySelectorAll(".answer_button")
        const textContent = this.props.value

        elements.forEach(function (element) {
            if (element.textContent == textContent) {
                if (isCompleted) element.classList.add("success")
                if (!isCompleted) element.classList.add("danger")
            } else {
                element.classList.remove("success")
                element.classList.remove("danger")
            }
        })
    }
}

AnswerButton.template = xml`
    <button t-on-click="onAction" class="answer_button sidebar-button">
        <t t-esc="props.value"/>
    </button>
`

AnswerButton.props = {
    ...standardFieldProps,
}
AnswerButton.supportedTypes = ["char"]

registry.category("fields").add("answer_button", AnswerButton)

// continue button
class ContinueButton extends Component {
    setup() {
        ;(this.res_id = this.props.record.data.id),
            (this.model_name = this.props.record.resModel),
            (this.orm = useService("orm"))
        this.action = useService("action")
    }

    async onAction() {
        await this.actionContinueVocabulary()
        this.removeAnswerButtonStatusClass()
    }

    removeAnswerButtonStatusClass() {
        const elements = document.querySelectorAll(".answer_button")

        elements.forEach(function (element) {
            element.classList.remove("success")
            element.classList.remove("danger")
        })
    }

    async actionContinueVocabulary() {
        try {
            const action = await this.orm.call(
                this.model_name,
                "continue_vocabulary",
                [this.res_id],
                {}
            )
            await this.props.record.model.root.load()
            await this.props.record.model.notify()
        } catch (error) {
            console.log("actionContinueVocabulary error: ", error)
        }
    }
}

ContinueButton.template = xml`
    <button t-on-click="onAction" class="continue_button sidebar-button">
        <t t-esc="props.value"/>
    </button>
`

ContinueButton.props = {
    ...standardFieldProps,
}
ContinueButton.supportedTypes = ["char"]

registry.category("fields").add("continue_button", ContinueButton)

// progress bar widget
class ProgressBar extends Component {}

ProgressBar.template = xml`
    <div class="progress-container">
        <div class="progress-bar" t-att-style="'width:' + props.value + '%'"></div>
    </div>
`

ProgressBar.props = {
    ...standardFieldProps,
}
ProgressBar.supportedTypes = ["integer"]

registry.category("fields").add("custom_progressbar", ProgressBar)
