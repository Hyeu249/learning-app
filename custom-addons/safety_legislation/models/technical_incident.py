# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from ...utilities.models import CONST as UTILITIES_CONST
from . import CONST
from odoo.exceptions import ValidationError
import logging


class TechnicalIncident(models.Model):
    _name = "legis.technical.incident"
    _description = "Technical incident records"
    _inherit = ["utilities.approval.status"]
    _check_company_auto = True

    finished_at = fields.Date("Finished at", tracking=True)
    repair_status = fields.Selection(
        CONST.REPAIR_STATUS,
        string="Repair status",
        default=CONST.PENDING,
        required=True,
        tracking=True,
    )
    technical_incident_html = fields.Html(
        "Technical incident html",
        default=lambda self: self._get_default_technical_incident_html(),
        tracking=True,
    )

    marine_protest_html = fields.Html(
        "Technical incident html",
        default=lambda self: self._get_default_marine_protest_html(),
        tracking=True,
    )
    is_insurace_involved = fields.Boolean("Is insurace involved", tracking=True)
    is_noti_for_legal_department = fields.Boolean(
        "is noti for legal department", tracking=True
    )
    insurance_deductible_cost = fields.Float("Insurance deductible cost", tracking=True)
    total_price = fields.Float("Total price", compute="_get_total_price", tracking=True)

    @api.depends("maintenance_scope_report_ids", "material_paint_quotes_request_ids")
    def _get_total_price(self):
        for record in self:
            if not record.are_all_reports_and_requests_approved():
                record.total_price = 0
            else:
                requests = record.material_paint_quotes_request_ids
                report_prices = record.maintenance_scope_report_ids.mapped(
                    "total_price"
                )
                request_prices = requests.mapped("total_prices")
                record.total_price = sum(report_prices + request_prices)

                if not record.is_noti_for_legal_department:
                    record._noti_for_legal_department()

    def _noti_for_legal_department(self):
        self.ensure_one()
        group_xml_id = "group_ship_head_of_legal"
        classes = "technical_incident_color"
        subject = f"Gợi ý bảo hiểm cho sự cố kỹ thuật!"
        body = f"Bản ghi {self.ref} cần yêu cầu bảo hiểm!"
        company_id = self.company_id

        self._send_notification_by_group_xml_and_company_id(
            group_xml_id, company_id, subject, body, classes
        )
        self.is_noti_for_legal_department = True

    def are_all_reports_and_requests_approved(
        self, at_least_one_report_or_request=False
    ):
        self.ensure_one()
        requests = self.material_paint_quotes_request_ids
        reports = self.maintenance_scope_report_ids
        approved_requests = requests.filtered(lambda e: e._is_approved_request())
        approved_reports = reports.filtered(lambda e: e._is_approved_report())
        requests_len = len(requests)
        reports_len = len(reports)
        approved_requests_len = len(approved_requests)
        approved_reports_len = len(approved_reports)
        have_one_report = reports_len >= 1
        have_one_request = requests_len >= 1
        at_least_one_report_or_request = have_one_report or have_one_request

        if (
            requests_len == approved_requests_len
            and reports_len == approved_reports_len
            and at_least_one_report_or_request
        ):
            return True
        else:
            return False

    # technical incident report fields
    trip = fields.Char("Trip", tracking=True)
    report_date = fields.Date("Report date", tracking=True)
    report_number = fields.Char("Report number", tracking=True)
    # for P.QLT
    assigned_cvkt = fields.Char("Assigned cvkt", tracking=True)
    director_comment_for_PQLT = fields.Char("Director comment for PQLT", tracking=True)
    # for SHIP
    department_in_charge = fields.Selection(
        CONST.DEPARTMENT_IN_CHARGE,
        string="Department in charge",
        default=CONST.MACHINERY,
        tracking=True,
    )
    maintenance_scope_ids = fields.Many2many(
        "ship.maintenance.scope", string="Maintenance scope", tracking=True
    )
    problem = fields.Char("Problem", tracking=True)
    temporary_action = fields.Char("Temporary action", tracking=True)
    recommend = fields.Char("Recommend", tracking=True)
    attachment_for_technical_incident = fields.Binary(
        "Attachment for technical incident", tracking=True
    )
    # others
    method = fields.Selection(
        CONST.TECHNICAL_INCIDENT_METHOD,
        string="Method",
        default=CONST.REPAIR_PROCESSING,
        tracking=True,
    )
    time = fields.Date("Time(waiting for materials + repair)", tracking=True)
    cost = fields.Float("Cost", tracking=True)
    origin = fields.Char("Origin", tracking=True)
    insurance = fields.Date("Insurance", tracking=True)

    # marine protest fields
    incident_date = fields.Date("Incident date", tracking=True)
    captain_name = fields.Char("Captain name", tracking=True)
    port_location = fields.Char("Port location", tracking=True)
    IMO = fields.Char("IMO", tracking=True)
    payload = fields.Char("Payload", tracking=True)
    port_of_registration = fields.Char("Port of registration", tracking=True)
    ship_owner = fields.Char("Ship owner", tracking=True)
    discoverer = fields.Char("Discoverer", tracking=True)
    address = fields.Char("Address", tracking=True)
    marine_protest_description = fields.Char(
        "Marine protest description", tracking=True
    )

    # relations
    technical_incident_job_ids = fields.One2many(
        "legis.technical.incident.job",
        "technical_incident_id",
        string="Technical incident job",
        tracking=True,
    )
    technical_incident_insurance_ids = fields.One2many(
        "legis.technical.incident.insurance",
        "technical_incident_id",
        string="Technical incident insurance",
        tracking=True,
    )
    maintenance_scope_report_ids = fields.Many2many(
        "ship.maintenance.scope.report",
        "ship_maintenance_scope_report_legis_technical_incident_rel",
        "technical_incident_id",
        "maintenance_scope_report_id",
        domain=f"[('technical_incident_id', '=', 0)]",
        string="Maintenance scope report",
        tracking=True,
    )
    material_paint_quotes_request_ids = fields.Many2many(
        "ship.material.paint.quotes.request",
        "ship_material_paint_quotes_request_legis_technical_incident_rel",
        "technical_incident_id",
        "material_paint_quotes_request_id",
        domain=f"[('technical_incident_id', '=', 0)]",
        string="Material paint quotes request",
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
            model_name = "legis.technical.incident"
            vals["ref"] = self.env["ir.sequence"].next_by_code(model_name)
        result = super(TechnicalIncident, self).create(vals_list)

        for record in result:
            record._on_off_approvals_base_on_conditions()
            report_added_ids = record.maintenance_scope_report_ids.ids
            record._handle_added_maintenance_scope_report_ids(report_added_ids)
            request_added_ids = record.material_paint_quotes_request_ids.ids
            record._handle_added_material_paint_quotes_request_ids(request_added_ids)

        return result

    def write(self, vals):
        self.ensure_one()
        old_report_ids = self.maintenance_scope_report_ids.ids
        old_request_ids = self.material_paint_quotes_request_ids.ids
        result = super(TechnicalIncident, self).write(vals)

        if self.are_only_approval_fields_changed(vals):
            return result

        new_report_ids = self.maintenance_scope_report_ids.ids
        new_request_ids = self.material_paint_quotes_request_ids.ids

        report_added_ids = set(new_report_ids) - set(old_report_ids)
        report_removed_ids = set(old_report_ids) - set(new_report_ids)
        request_added_ids = set(new_request_ids) - set(old_request_ids)
        request_removed_ids = set(old_request_ids) - set(new_request_ids)

        if report_added_ids:
            self._handle_added_maintenance_scope_report_ids(list(report_added_ids))
        if report_removed_ids:
            self._handle_removed_maintenance_scope_report_ids(list(report_removed_ids))

        if request_added_ids:
            self._handle_added_material_paint_quotes_request_ids(
                list(request_added_ids)
            )
        if request_removed_ids:
            self._handle_removed_material_paint_quotes_request_ids(
                list(request_removed_ids)
            )

        if "repair_status" in vals:
            self._on_off_approvals_base_on_conditions()

        if "technical_incident_html" not in vals and "marine_protest_html" not in vals:
            self.rerender_technical_incident_html()
            self.rerender_marine_protest_html()

        return result

    def rerender_technical_incident_html(self):
        self.ensure_one()
        placeholders = {
            "trip": self.trip,
            "report_date ": self.report_date,
            "report_number": self.report_number,
            "assigned_cvkt": self.assigned_cvkt,
            "director_comment_for_PQLT": self.director_comment_for_PQLT,
            "department_in_charge": self.department_in_charge,
            "maintenance_scope": ",".join(self.maintenance_scope_ids.mapped("name")),
            "problem": self.problem,
            "temporary_action": self.temporary_action,
            "recommend": self.recommend,
            "method": self.method,
            "time": self.time,
            "cost": self.cost,
            "origin": self.origin,
            "insurance": self.insurance,
        }

        self.technical_incident_html = (
            self._get_default_technical_incident_html().format(**placeholders)
        )

    def rerender_marine_protest_html(self):
        self.ensure_one()
        placeholders = {
            "incident_date": self.incident_date,
            "captain_name": self.captain_name,
            "port_location": self.port_location,
            "IMO": self.IMO,
            "payload": self.payload,
            "port_of_registration": self.port_of_registration,
            "ship_owner": self.ship_owner,
            "discoverer": self.discoverer,
            "address": self.address,
            "marine_protest_description": self.marine_protest_description,
        }

        self.marine_protest_html = self._get_default_marine_protest_html().format(
            **placeholders
        )

    def _on_off_approvals_base_on_conditions(self):
        self.ensure_one()
        if self.repair_status == CONST.PENDING:
            self._off_approval()

        elif self.repair_status == CONST.FIXABLE:
            self._on_approval()

        elif self.repair_status == CONST.UNFIXABLE:
            self._off_approval()

    def name_get(self):
        result = []
        for report in self:
            name = report.ref or _("New")
            result.append((report.id, name))
        return result

    def _handle_added_maintenance_scope_report_ids(self, added_ids):
        self.ensure_one()
        for id in added_ids:
            report = self.maintenance_scope_report_ids.browse(id)
            report.technical_incident_id = self.id

    def _handle_removed_maintenance_scope_report_ids(self, removed_ids):
        self.ensure_one()
        for id in removed_ids:
            report = self.maintenance_scope_report_ids.browse(id)
            report.technical_incident_id = False

    def remove_report_by_id(self, id=False):
        self.ensure_one()
        if id == False:
            return
        report = self.maintenance_scope_report_ids.filtered(lambda e: e.id == id)
        self.maintenance_scope_report_ids -= report

    def _handle_added_material_paint_quotes_request_ids(self, added_ids):
        self.ensure_one()
        for id in added_ids:
            request = self.material_paint_quotes_request_ids.browse(id)
            request.technical_incident_id = self.id

    def _handle_removed_material_paint_quotes_request_ids(self, removed_ids):
        self.ensure_one()
        for id in removed_ids:
            request = self.material_paint_quotes_request_ids.browse(id)
            request.technical_incident_id = False

    def remove_request_by_id(self, id=False):
        self.ensure_one()
        if id == False:
            return
        request = self.material_paint_quotes_request_ids.filtered(lambda e: e.id == id)
        self.material_paint_quotes_request_ids -= request

    def _get_default_technical_incident_html(self):
        default_value_model = self._get_default_value_model()
        variable_name = UTILITIES_CONST.HTML_TECHNICAL_INCIDENT_CONTENT
        table = 'class="table table-bordered o_table"'
        replace_table = f'{table} style="margin-bottom:0px"'

        html = default_value_model._get_default_value_by_variable_name(variable_name)
        return str(html).replace(table, replace_table)

    def _get_default_marine_protest_html(self):
        default_value_model = self._get_default_value_model()
        variable_name = UTILITIES_CONST.HTML_TECHNICAL_INCIDENT_MARINE_PROTEST_CONTENT
        table = 'class="table table-bordered o_table"'
        replace_table = f'{table} style="margin-bottom:0px"'

        html = default_value_model._get_default_value_by_variable_name(variable_name)
        return str(html).replace(table, replace_table)
