from odoo import fields, models, api, _
from .. import CONST


class ShipMaterialAssignmentLegisTechnicalIncidentJobRel(models.Model):
    _name = "ship.material.assignment.legis.technical.incident.job.rel"
    _description = "Ship material assignment legis technical incident job rel"
    _inherit = ["utilities.notification"]

    material_assignment_id = fields.Many2one(
        "ship.material.assignment",
        string="Material assignment",
        required=True,
    )
    technical_incident_job_id = fields.Many2one(
        "legis.technical.incident.job",
        string="Technical incident job",
        required=True,
    )

    # Define SQL constraint
    _sql_constraints = [
        (
            "unique_material_assignment_id",
            "unique (material_assignment_id)",
            "material_assignment_id must be unique.",
        ),
    ]
