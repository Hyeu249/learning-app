# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from ...utilities.models import CONST as UTILITIES_CONST
from . import CONST
from odoo.exceptions import ValidationError


class TechnicalIncidentJob(models.Model):
    _name = "legis.technical.incident.job"
    _description = "Technical incident job records"
    _inherit = ["utilities.notification"]
    _check_company_auto = True

    name = fields.Char("Name", tracking=True)
    description = fields.Char("Description", tracking=True)
    finished_at = fields.Date("Finished at", tracking=True)

    # relations
    technical_incident_id = fields.Many2one(
        "legis.technical.incident",
        string="Technical incident",
        tracking=True,
    )
    material_assignment_ids = fields.Many2many(
        "ship.material.assignment",
        "ship_material_assignment_legis_technical_incident_job_rel",
        "technical_incident_job_id",
        "material_assignment_id",
        domain=f"[('job_quote_id', '=', False), ('technical_incident_job_id', '=', 0)]",
        string="Material assignment",
        tracking=True,
    )

    # company
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            model_name = "legis.technical.incident.job"
            vals["ref"] = self.env["ir.sequence"].next_by_code(model_name)
        result = super(TechnicalIncidentJob, self).create(vals_list)

        for record in result:
            assignment_added_ids = [a.id for a in record.material_assignment_ids]
            record._handle_added_material_assignments(assignment_added_ids)

        return result

    def write(self, vals):
        self.ensure_one()
        old_assignment_ids = self.material_assignment_ids.ids
        result = super(TechnicalIncidentJob, self).write(vals)
        new_assignment_ids = self.material_assignment_ids.ids

        assignment_added_ids = set(new_assignment_ids) - set(old_assignment_ids)
        assignment_removed_ids = set(old_assignment_ids) - set(new_assignment_ids)

        if assignment_added_ids:
            self._handle_added_material_assignments(list(assignment_added_ids))
        if assignment_removed_ids:
            self._handle_removed_material_assignments(list(assignment_removed_ids))

        return result

    def name_get(self):
        result = []
        for report in self:
            name = report.ref or _("New")
            result.append((report.id, name))
        return result

    def _handle_added_material_assignments(self, added_ids):
        self.ensure_one()
        for id in added_ids:
            material_assignment_id = self.material_assignment_ids.browse(id)
            material_assignment_id.technical_incident_job_id = self.id

    def _handle_removed_material_assignments(self, removed_ids):
        self.ensure_one()
        for id in removed_ids:
            material_assignment_id = self.material_assignment_ids.browse(id)
            material_assignment_id.technical_incident_job_id = False

    def remove_assignment_by_id(self, id=False):
        self.ensure_one()
        if id == False or id == 0:
            return
        material_assignment_id = self.material_assignment_ids.filtered(
            lambda e: e.id == id
        )
        self.material_assignment_ids -= material_assignment_id
