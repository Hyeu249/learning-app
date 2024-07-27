from odoo import fields, models, api, _
from .. import CONST


class ShipMaterialPaintQuotesRequestLegisTechnicalIncidentRel(models.Model):
    _name = "ship.material.paint.quotes.request.legis.technical.incident.rel"
    _description = "Ship material paint quotes request legis technical incident rel"
    _inherit = ["utilities.notification"]

    material_paint_quotes_request_id = fields.Many2one(
        "ship.material.paint.quotes.request",
        string="Material paint quotes request",
        required=True,
    )
    technical_incident_id = fields.Many2one(
        "legis.technical.incident",
        string="Technical incident",
        required=True,
    )

    # Define SQL constraint
    _sql_constraints = [
        (
            "unique_material_paint_quotes_request_id",
            "unique (material_paint_quotes_request_id)",
            "material_paint_quotes_request_id must be unique.",
        ),
    ]
