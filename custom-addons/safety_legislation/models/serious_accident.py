# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST


class SeriousAccident(models.Model):
    _name = "legis.serious.accident"
    _description = "Serious accident records"
    _inherit = ["utilities.notification"]
    _check_company_auto = True

    accident_report_html = fields.Html("Accident report html", tracking=True)
    initial_investigation_report_html = fields.Html(
        "Initial investigation report html", tracking=True
    )
    ert_checklist_html = fields.Html("Ert checklist html", tracking=True)
    marine_protest_html = fields.Html("Marine protest html", tracking=True)

    # relations
    ert_task_ids = fields.One2many(
        "legis.ert.task",
        "serious_accident_id",
        string="Ert task",
        tracking=True,
    )

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    # company
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            model_name = "legis.serious.accident"
            vals["ref"] = self.env["ir.sequence"].next_by_code(model_name)
        result = super(SeriousAccident, self).create(vals_list)

        return result

    def name_get(self):
        result = []
        for report in self:
            name = report.ref or _("New")
            result.append((report.id, name))
        return result
