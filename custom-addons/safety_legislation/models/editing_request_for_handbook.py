# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST
from odoo.exceptions import ValidationError
import logging


class EditingRequestForHandbook(models.Model):
    _name = "legis.editing.request.for.handbook"
    _description = "Editing request for handbook records"
    _inherit = ["utilities.approval.status"]
    _check_company_auto = True

    request_date = fields.Date(string="Request date", tracking=True)
    is_hide_content_old_new_diff = fields.Boolean(
        string="Is hide content old new diff",
        default=True,
        tracking=True,
    )

    # relations
    safety_management_handbook_id = fields.Many2one(
        "legis.safety.management.handbook",
        string="Safety management handbook",
        tracking=True,
    )
    changed_content_of_handbook_ids = fields.One2many(
        "legis.changed.content.of.handbook",
        "editing_request_for_handbook_id",
        string="Changed Content Of Handbook",
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
            model_name = "legis.editing.request.for.handbook"
            vals["ref"] = self.env["ir.sequence"].next_by_code(model_name)
        result = super(EditingRequestForHandbook, self).create(vals_list)

        return result

    def name_get(self):
        result = []
        for report in self:
            name = report.ref or _("New")
            result.append((report.id, name))
        return result

    def get_changed_content_of_handbook(self):
        self.ensure_one()
        handbook_id = self.safety_management_handbook_id

        self.changed_content_of_handbook_ids.unlink()
        for section in handbook_id.handbook_section_ids:
            section.recursive_action(
                self.create_changed_content_of_handbook_based_on_modified_section_version
            )

    def create_changed_content_of_handbook_based_on_modified_section_version(
        self, section_id, return_result=False
    ):
        self.ensure_one()
        modified_version_id = section_id.modified_section_version_id

        if modified_version_id:
            self.create_changed_content_of_handbook(section_id, modified_version_id)

    def create_changed_content_of_handbook(self, existing_content_id, change_to_id):
        self.ensure_one()
        self.env["legis.changed.content.of.handbook"].create(
            {
                "editing_request_for_handbook_id": self.id,
                "control_number": existing_content_id.control_number,
                "existing_handbook_section_content_id": existing_content_id.id,
                "handbook_section_change_to_id": change_to_id.id,
            }
        )

    def create_new_handbook(self):
        self.ensure_one()
        return self.env["legis.safety.management.handbook"].create({})

    def create_new_handbook_based_on_request(self):
        self.ensure_one()

        if not self._is_approved():
            raise ValidationError("Yêu cầu chưa được duyệt, vui lòng kiểm tra lại!")

        old_handbook_id = self.safety_management_handbook_id
        new_handbook_id = self.create_new_handbook()

        for section in old_handbook_id.handbook_section_ids:
            section.recursive_action(
                self.copy_or_create_new_handbook_section,
                (CONST.SECTION_FOR_HANDBOOK, new_handbook_id.id),
            )

    def copy_or_create_new_handbook_section(self, section_id, return_result=False):
        self.ensure_one()
        if return_result:
            first_value = return_result[0]
            second_value = return_result[1]
            modified_section_id = section_id.modified_section_version_id

            control_number = section_id.control_number
            title = section_id.title
            content = section_id.content

            if modified_section_id:
                approved_section = self.check_revision_state_of_current_section(
                    section_id
                )

                if approved_section:
                    control_number = modified_section_id.control_number
                    title = modified_section_id.title
                    content = modified_section_id.content

            if first_value == CONST.SECTION_FOR_HANDBOOK:
                new_section_id = self.create_handbook_section(
                    control_number, title, content, handbook_id=second_value
                )
                if section_id.are_need_metas:
                    new_section_id.are_need_metas = section_id.are_need_metas
                    section_id.set_ert_role_meta_ids_to_new_section(new_section_id)
                    section_id.set_incidence_type_meta_ids_to_new_section(
                        new_section_id
                    )
                return (CONST.SECTION_FOR_PARENT_SECTION, new_section_id.id)
            if first_value == CONST.SECTION_FOR_PARENT_SECTION:
                new_section_id = self.create_handbook_section(
                    control_number, title, content, parent_section_id=second_value
                )
                if section_id.are_need_metas:
                    new_section_id.are_need_metas = section_id.are_need_metas
                    section_id.set_ert_role_meta_ids_to_new_section(new_section_id)
                    section_id.set_incidence_type_meta_ids_to_new_section(
                        new_section_id
                    )
                return (CONST.SECTION_FOR_PARENT_SECTION, new_section_id.id)

    def create_handbook_section(
        self, control_number, title, content, handbook_id=False, parent_section_id=False
    ):
        self.ensure_one()

        result = {
            "control_number": control_number,
            "title": title,
            "content": content,
            "safety_management_handbook_id": handbook_id,
            "handbook_parent_section_id": parent_section_id,
        }
        return self.env["legis.handbook.section"].create(result)

    def check_revision_state_of_current_section(self, current_section_id):
        self.ensure_one()
        changed_content = self.changed_content_of_handbook_ids.filtered(
            lambda e: e.existing_handbook_section_content_id == current_section_id
        )

        if changed_content.revision_state == CONST.APPROVED_HANDBOOK_SECTION_VERSION:
            return True
        else:
            return False
