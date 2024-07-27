/** @odoo-module */

import {
    Component,
    xml,
    useState,
    onWillUpdateProps,
    onMounted,
} from "@odoo/owl"
import { registry } from "@web/core/registry"
import { useService } from "@web/core/utils/hooks"
import { Header, Body } from "./components"

class LearningAppHome extends Component {
    static components = { Header, Body }

    setup() {
        onMounted(this.onMounted)
    }

    onMounted() {}
}

LearningAppHome.template = "LearningAppHome"

registry.category("actions").add("action_lang_app", LearningAppHome)
