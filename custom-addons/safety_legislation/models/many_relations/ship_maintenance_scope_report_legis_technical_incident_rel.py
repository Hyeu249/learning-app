from odoo import fields, models, api, _
from .. import CONST


class ShipMaintenanceScopeReportLegisTechnicalIncidentRel(models.Model):
    _name = "ship.maintenance.scope.report.legis.technical.incident.rel"
    _description = "Ship maintenance scope report legis technical incident rel"
    _inherit = ["utilities.notification"]

    maintenance_scope_report_id = fields.Many2one(
        "ship.maintenance.scope.report",
        string="Maintenance scope report",
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
            "unique_maintenance_scope_report_id",
            "unique (maintenance_scope_report_id)",
            "maintenance_scope_report_id must be unique.",
        ),
    ]
