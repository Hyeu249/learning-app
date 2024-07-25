# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST


class SeriousAccidentTask(models.Model):
    _name = "legis.serious.accident.task"
    _description = "Serious accident task records"
    _inherit = ["utilities.notification"]
    _check_company_auto = True

    name = fields.Char(string="Name", tracking=True)
    description = fields.Char(string="Description", tracking=True)

    # relations
    ert_task_id = fields.Many2one("legis.ert.task", string="Ert task", tracking=True)

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    # company
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            model_name = "legis.serious.accident.task"
            vals["ref"] = self.env["ir.sequence"].next_by_code(model_name)
        result = super(SeriousAccidentTask, self).create(vals_list)

        return result

    def name_get(self):
        result = []
        for report in self:
            name = report.ref or _("New")
            result.append((report.id, name))
        return result
