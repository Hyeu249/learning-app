# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST


class ErtTask(models.Model):
    _name = "legis.ert.task"
    _description = "Ert task records"
    _inherit = ["utilities.notification"]
    _check_company_auto = True

    # relations
    group_id = fields.Many2one("res.groups", string="Role", tracking=True)
    serious_accident_task_ids = fields.One2many(
        "legis.serious.accident.task",
        "ert_task_id",
        string="Serious Accident Task",
        tracking=True,
    )
    serious_accident_id = fields.Many2one(
        "legis.serious.accident",
        string="Serious accident",
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
            model_name = "legis.ert.task"
            vals["ref"] = self.env["ir.sequence"].next_by_code(model_name)
        result = super(ErtTask, self).create(vals_list)

        return result

    def name_get(self):
        result = []
        for report in self:
            name = report.ref or _("New")
            result.append((report.id, name))
        return result
