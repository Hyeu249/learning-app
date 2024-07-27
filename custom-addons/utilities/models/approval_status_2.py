# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST
from odoo.exceptions import ValidationError
import logging
from datetime import timedelta, datetime

SUPER_ADMIN_GROUP_EXTERN_ID = "utilities.group_ship_admin"


class ApprovalStatus(models.Model):
    _name = "utilities.approval.status.hello"
    _description = "Approval status records"
    _inherit = ["utilities.notification"]
    _sudo_field_permission_list = {}

    approval_status = fields.Selection(
        "_get_approval_status",
        string="Approval status",
        tracking=True,
    )

    xml_id = fields.Char(string="Group xml id", compute="_get_xml_id", store=True)

    def _get_approval_status(self):
        selection = self._approval_flow_selection()
        selection.append((CONST.REJECTED, "Rejected"))
        selection.append((CONST.APPROVED, "Approved"))
        return selection

    def _approval_flow_selection(self):
        approval_flow_id = self._get_approval_flow_id()
        level_ids = approval_flow_id.approval_level_ids
        selection = [(self.get_section_value(level), level.name) for level in level_ids]

        return selection

    def get_section_value(self, level, get_int=False):
        group_id = self.level_to_group_id(level)
        if level.second_time:
            return f"{group_id}-s"
        else:
            if get_int:
                return group_id
            else:
                return str(group_id)

    def level_to_group_id(self, level):
        return level.user_group.id

    @api.depends("approval_status")
    def _get_xml_id(self):
        for record in self:
            group_id = record._get_current_group_id()
            group = self.env["res.groups"].browse(group_id)
            xml_id = "EMPTY.EMPTY"
            if group:
                xml_id = list(group.ensure_one().get_xml_id().values())[0]

            record.xml_id = xml_id

    @api.depends("approval_status")
    def _get_is_in_approval_flow(self):
        role_ids = [status[0] for status in self._approval_flow_selection()]
        last_role_id = role_ids[-1]

        for record in self:
            status = record.approval_status

            if status not in role_ids or status == last_role_id:
                record.is_in_approval_flow = False
            else:
                record.is_in_approval_flow = True

    def get_group(self):
        group_id = self._get_current_group_id()
        group = self.env["res.groups"].browse(group_id)
        return group

    name_for_noti = fields.Char("Name for noti")
    is_off_approval = fields.Boolean("Is off approval", default=False)
    is_in_approval_flow = fields.Boolean(
        "Is in approval flow", compute="_get_is_in_approval_flow"
    )

    # relations
    approval_flow_id = fields.Many2one(
        "utilities.approval.flow", string="Approval flow"
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("approval_status"):
                vals["approval_status"] = self.get_first_approval_role()

        result = super(ApprovalStatus, self).create(vals_list)

        return result

    def get_first_approval_role(self):
        group_id_array = self._approval_selection_value_array()
        if group_id_array:
            return group_id_array[0]

    def get_current_next_and_role_ids_of_approval_status(self, vals):
        self.ensure_one()
        role_ids = self._approval_selection_value_array()
        old_status = self.approval_status
        new_status = vals.get("approval_status")

        return old_status, new_status, role_ids

    def get_indexes_of_current_and_next_approval_status(self, vals):
        """
        This function is used to get the indexes of current user's role and the next role in the approval flow.
        """
        self.ensure_one()
        old_status, new_status, role_ids = (
            self.get_current_next_and_role_ids_of_approval_status(vals)
        )

        if self.is_in_proposal_flow(vals):
            old_index = role_ids.index(old_status)
            new_index = role_ids.index(new_status)

            return old_index, new_index, role_ids
        else:
            return None, None, None

    def get_difference_of_current_and_next_approval_status_index(self, vals):
        """
        Calculate the absolute difference between the index of the current approval status
        and the index of the next approval status.
        """
        self.ensure_one()
        old_index, new_index, _ = self.get_indexes_of_current_and_next_approval_status(
            vals
        )

        if old_index != None and new_index != None:
            return abs(old_index - new_index)
        else:
            return False

    def get_group_ids_between_current_and_next_approval_status_index(self, vals):
        """
        Retrieve the group IDs that are between the current approval status index
        and the next approval status index.
        """
        self.ensure_one()
        old_index, new_index, role_ids = (
            self.get_indexes_of_current_and_next_approval_status(vals)
        )

        if old_index != None and new_index != None:

            if old_index < new_index:
                return role_ids[old_index + 1 : new_index]
            elif old_index > new_index:
                return role_ids[new_index + 1 : old_index]
        else:
            return []

    def supplier_level_between_current_and_next_approval_status(self, vals):
        self.ensure_one()
        supplier_group_id = self.get_group_id_by_xml_id(f"utilities.{CONST.SUPPLIER}")

        str_group_ids = (
            self.get_group_ids_between_current_and_next_approval_status_index(vals)
        )

        return str(supplier_group_id) in str_group_ids

    def not_allow_user_to_propose_more_than_1_level(self, vals):
        """
        Check if the user is not allowed to propose changes that span more than one approval level.
        """
        self.ensure_one()
        if self.get_difference_of_current_and_next_approval_status_index(vals) >= 2:
            raise ValidationError(f"Không thể đẩy từ 2 cấp độ trở lên!")

    def validate_approval_flow(self, vals):
        self.ensure_one()
        not_validate_approval_flow = self.env.context.get("not_validate_approval_flow")
        message = f"Không có quyền thao thác, vui lòng gửi lại hoặc liên hệ admin!"

        if not_validate_approval_flow:
            # allow proposing
            return

        if self.is_in_proposal_flow(vals):
            self.not_allow_user_to_propose_more_than_1_level(vals)

        # elif self.is_leave_from_approve_or_reject_process(vals):
        #     if not self.is_move_to_penultimate_level(vals):
        #         raise ValidationError(message)

        elif self.is_move_to_approve_or_reject_process(vals):
            if not self.is_move_from_last_level(vals):
                raise ValidationError(message)

    def is_move_to_approve_or_reject_process(self, vals):
        old_status, new_status, role_ids = (
            self.get_current_next_and_role_ids_of_approval_status(vals)
        )

        return old_status in role_ids and (
            new_status == CONST.APPROVED or new_status == CONST.REJECTED
        )

    def is_leave_from_approve_or_reject_process(self, vals):
        old_status, new_status, role_ids = (
            self.get_current_next_and_role_ids_of_approval_status(vals)
        )

        return new_status in role_ids and (
            old_status == CONST.APPROVED or old_status == CONST.REJECTED
        )

    def is_move_to_penultimate_level(self, vals):
        self.ensure_one()
        old_status, new_status, role_ids = (
            self.get_current_next_and_role_ids_of_approval_status(vals)
        )

        return new_status == role_ids[-2]

    def is_move_from_last_level(self, vals):
        self.ensure_one()
        old_status, new_status, role_ids = (
            self.get_current_next_and_role_ids_of_approval_status(vals)
        )
        return old_status == role_ids[-1]

    def is_in_proposal_flow(self, vals):
        self.ensure_one()
        old_status, new_status, role_ids = (
            self.get_current_next_and_role_ids_of_approval_status(vals)
        )

        return old_status in role_ids and new_status in role_ids

    def verify_user_permission(self, vals):
        """
        Verify if the current user is allowed to edit the record.

        Raises:
            odoo.exceptions.ValidationError: If the user is not allowed to edit.
        """
        self.ensure_one()
        sudo_field = self.env.context.get("sudo_field")

        if sudo_field:
            return
        elif self.are_all_sudo_field_permission_list(vals):
            self.check_user_permission_in_sudo_field_permission_list(vals)
            return
        else:
            self._check_if_current_user_allowed_to_perform()

    def check_user_permission_in_sudo_field_permission_list(self, vals):
        """
        Checks if the current user has permissions in the sudo field permission list.

        Raises:
            odoo.exceptions.AccessDenied: If the current user does not have permissions in sudo fields.
        """
        self.ensure_one()

        for field_name, group_xml_ids in self._sudo_field_permission_list.items():
            if field_name not in vals:
                continue
            if group_xml_ids == []:
                # allow editing
                pass
            else:
                if not self.user_has_any_group(group_xml_ids):
                    self._check_if_current_user_allowed_to_perform()

    def user_has_any_group(self, group_xml_ids):
        """
        Checks if the current user has any of the provided groups.

        Args:
            group_xml_ids (list): List of group xml ids to check.

        Returns:
            bool: True if the user has any of the provided groups, False otherwise.
        """
        self.ensure_one()

        return any(
            [self.env.user.has_group(group_xml_id) for group_xml_id in group_xml_ids]
        )

    def are_all_sudo_field_permission_list(self, field_names):
        """
        Check if all field_names belong to sudo fields in the permission list.

        Args:
            vals (iterable): The field names to check.

        Returns:
            bool: True if all field names belong to sudo fields, False otherwise.
        """
        self.ensure_one()
        sudo_fields = self._sudo_field_permission_list.keys()

        return all(field_name in sudo_fields for field_name in field_names)

    def write(self, vals):
        for record in self:
            record.validate_approval_flow(vals)
            record.verify_user_permission(vals)

        result = super(ApprovalStatus, self).write(vals)

        for record in self:
            if record.is_off_approval:
                return result

            if not record._get_approval_flow_id():
                return result

            if not self.is_it_only_approval_fields_that_have_changed(vals):
                record._edited_record_notification(vals)
            elif "approval_status" in vals:
                record._propose_request_notification()

            if "approval_status" in vals:
                model_name = "utilities.model_utilities_default_value"
                name = f"Approval reminder notification {record._name}-{record.ref}"
                model_id = self.env.ref(model_name).id
                if record._is_approved():
                    record._send_noti_for_people_after_approve_record()

                if record._is_approved() or record._is_rejected():
                    record.remove_approval_reminder_notification_cron(name, model_id)
                else:
                    record.approval_reminder_notification_cron(name, model_id)

        return result

    def unlink(self):
        for record in self:
            model_name = "utilities.model_utilities_default_value"
            name = f"Approval reminder notification {self._name}-{record.ref}"
            model_id = self.env.ref(model_name).id
            record.remove_approval_reminder_notification_cron(name, model_id)
        return super(ApprovalStatus, self).unlink()

    def remove_approval_reminder_notification_cron(self, name, model_id):
        cron_job = (
            self.env["ir.cron"]
            .sudo()
            .search(
                [
                    ("name", "=", name),
                    ("model_id", "=", model_id),
                ]
            )
        )

        if cron_job:
            cron_job.sudo().unlink()

    def approval_reminder_notification_cron(self, name, model_id):
        self.ensure_one()
        timeout = timedelta(seconds=10)
        scheduled_time = datetime.now() + timeout

        self.remove_approval_reminder_notification_cron(name, model_id)
        group_xml_id = self.xml_id
        context = {
            "group_id": self._get_current_group_id(),
            "model_name": self._name,
            "record_id": self.id,
        }
        default_model = self._get_default_value_model()
        variable_name_1 = (
            CONST.INTEGER_APPROVAL_STATUS_INTERVAL_NUMBER_TIME_FOR_APPROVER
        )
        variable_name_2 = CONST.STRING_APPROVAL_STATUS_INTERVAL_TYPE_TIME_FOR_APPROVER
        interval_number = (
            default_model._get_default_value_by_variable_name(variable_name_1) or 2
        )
        interval_type = (
            default_model._get_default_value_by_variable_name(variable_name_2)
            or "hours"
        )

        self.env["ir.cron"].sudo().create(
            {
                "name": name,
                "model_id": model_id,
                "type": "ir.actions.server",
                "state": "code",
                "code": f"model.with_context({context}).send_a_reminder_to_the_current_approver()",
                "active": True,
                "nextcall": scheduled_time.strftime("%Y-%m-%d %H:%M:%S"),
                "interval_number": interval_number,
                "interval_type": interval_type,
                "numbercall": "-1",
            }
        )

    def _send_inbox(self, group_id):
        self.ensure_one()
        group_id = group_id
        company_id = self.sudo().company_id
        subject = f"Yêu cầu duyệt từ {self._description}"
        message = f"Bản ghi cần được duyệt!"

        self._send_notification_by_group_id_and_company_id(
            group_id, company_id, subject, message
        )

    def send_an_email_to_remind_the_current_approver(self, group_id, user_id):
        self.ensure_one()
        template = self.env.ref("utilities.email_to_remind_the_current_approver").id
        role_id = self.env["res.groups"].browse(group_id)

        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        record_url = f"{base_url}/web#id={self.id}&view_type=form&model={self._name}"

        context = {
            "self": self,
            "role_name": role_id.name,
            "record_url": record_url,
        }
        email_values = {
            "email_to": user_id.email,
        }
        (
            self.env["mail.template"]
            .browse(template)
            .with_context(context)
            .send_mail(self.id, email_values=email_values, force_send=False)
        )

    def _send_noti_for_people_after_approve_record(self):
        self.ensure_one()
        default_value_model = self._get_default_value_model()
        variable_name = CONST.USERS_APPROVAL_STATUS_NOTIFICATION_FOR_APPROVED
        user_ids = default_value_model._get_default_value_by_variable_name(
            variable_name
        )

        classes = "title_approved_color"
        subject = "Đơn đã duyệt xong!!"
        message = f"Vui lòng kiểm tra bản ghi {self.ref}!!"

        for user in user_ids:
            self._send_notification_by_user(user, subject, message, classes)

    def _get_default_value_model(self):
        model_name = "utilities.default.value"
        default_value_model = self.env[model_name].search([])

        return default_value_model

    def is_it_only_approval_fields_that_have_changed(self, vals):
        approval_model_fields = [
            "approval_status",
            "name_for_noti",
            "is_off_approval",
            "xml_id",
            "is_in_approval_flow",
            "approval_flow_id",
        ]

        is_it_only_approval_fields_that_have_changed = all(
            x in approval_model_fields for x in vals
        )

        if is_it_only_approval_fields_that_have_changed:
            return True
        else:
            return False

    def _propose_request_notification(self):
        self.ensure_one()
        group_id = self._get_current_group_id()
        company_id = self.company_id
        group = self.get_group()
        name_for_noti = f"({self.name_for_noti})" if self.name_for_noti else ""
        classes = "title_request_color"
        subject = f"{self._description}(đề xuất)"
        message = (
            f"Bản ghi {self.ref}{name_for_noti} cần được xem qua bởi {group.name}!"
        )

        self._send_notification_by_group_id_and_company_id(
            group_id, company_id, subject, message, classes
        )

    def _edited_record_notification(self, vals):
        edit_what = ",".join(vals)
        group_ids = self._get_group_ids_for_edit_notification()
        company_id = self.company_id
        current_user = self.env.user
        name_for_noti = f"({self.name_for_noti})" if self.name_for_noti else ""
        classes = "title_quote_color"
        subject = f"{self._description}(chỉnh sửa)"
        message = f"Bản ghi {self.ref}{name_for_noti} đã chỉnh sửa {edit_what} bởi {current_user.name}!"

        for group_id in group_ids:
            self._send_notification_by_group_id_and_company_id(
                group_id, company_id, subject, message, classes
            )

    def _get_group_ids_for_edit_notification(self):
        approval_level_ids = self._get_approval_flow_id().approval_level_ids
        group_ids = [level_id.user_group.id for level_id in approval_level_ids]

        current_group_id = self._get_current_group_id()

        if current_group_id:
            index = group_ids.index(current_group_id)
            group_ids_for_notification = group_ids[0:index]
            return group_ids_for_notification
        else:
            return []

    def _get_current_group_id(self):
        status = self.approval_status
        approved = status == CONST.APPROVED
        rejected = status == CONST.REJECTED
        pending = status == CONST.PENDING

        selection = self._approval_flow_selection()

        if selection and status:
            last_level_flow = selection[-1]
            value_last_level_flow = last_level_flow[0]

            if approved or rejected:
                if "-s" in value_last_level_flow:
                    group_id = value_last_level_flow.split("-")[0]
                    return int(group_id)
                else:
                    return int(value_last_level_flow)
            elif pending:
                return 0
            else:
                if "-s" in status:
                    group_id = status.split("-")[0]
                    return int(group_id)
                else:
                    return int(status)
        else:
            return 0

    def name_get(self):
        result = []
        for report in self:
            name = report.ref or _("New")
            result.append((report.id, name))
        return result

    def _check_if_current_user_allowed_to_perform(self):
        self.ensure_one()
        user_has_admin_group = self.env.user.has_group(SUPER_ADMIN_GROUP_EXTERN_ID)
        if user_has_admin_group:
            return True

        user_has_group = self.env.user.has_group(self.xml_id)
        message = "Không có quyền thao tác, vui lòng liên hệ admin!"

        if not user_has_group:
            raise ValidationError(message)
        return False

    def action_propose(self):
        self.ensure_one()
        role_ids = [status[0] for status in self._approval_flow_selection()]
        status = self.approval_status
        last_role_id = role_ids[-1]

        if status in role_ids and status != last_role_id:
            index = role_ids.index(status)
            self.approval_status = role_ids[index + 1]

    def action_propose_two_level(self):
        self.ensure_one()
        role_ids = [status[0] for status in self._approval_flow_selection()]
        status = self.approval_status
        second_last_role_id = role_ids[-2]
        last_role_id = role_ids[-1]

        if (
            status in role_ids
            and status != second_last_role_id
            and status != last_role_id
        ):
            index = role_ids.index(status)
            self.approval_status = role_ids[index + 2]

    def action_unpropose_two_level(self):
        self.ensure_one()
        role_ids = [status[0] for status in self._approval_flow_selection()]
        status = self.approval_status
        first_role_id = role_ids[0]
        second_first_role_id = role_ids[1]

        if (
            status in role_ids
            and status != first_role_id
            and status != second_first_role_id
        ):
            index = role_ids.index(status)
            self.approval_status = role_ids[index - 2]

        elif self._is_approved() or self._is_rejected():
            self.approval_status = role_ids[-2]

    def action_unpropose(self):
        self.ensure_one()
        role_ids = [status[0] for status in self._approval_flow_selection()]
        status = self.approval_status
        first_role_id = role_ids[0]

        if status in role_ids and status != first_role_id:
            index = role_ids.index(status)
            self.approval_status = role_ids[index - 1]

        elif self._is_approved() or self._is_rejected():
            self.approval_status = role_ids[-2]

    def action_approve(self):
        self.ensure_one()
        self._approved()

    def action_reject(self):
        self.ensure_one()
        self._rejected()

    def restart_flow(self):
        self.ensure_one()
        first_level_flow = self._approval_flow_selection()[0]
        first_level_flow_value = first_level_flow[0]

        self.sudo_field().approval_status = first_level_flow_value

    def sudo_field(self):
        self.ensure_one()
        context = dict(self.env.context)
        context.update({"sudo_field": True})

        return self.with_context(context)

    def not_validate_approval_flow(self):
        self.ensure_one()
        context = dict(self.env.context)

        context.update({"not_validate_approval_flow": True})

        return self.with_context(context)

    def sudo_approve(self):
        self.sudo_field().not_validate_approval_flow().approval_status = CONST.APPROVED

    def _approved(self):
        self.approval_status = CONST.APPROVED

    def _rejected(self):
        self.approval_status = CONST.REJECTED

    def _is_approved(self):
        return self.approval_status == CONST.APPROVED

    def _is_rejected(self):
        return self.approval_status == CONST.REJECTED

    def _get_approval_flow_id(self):
        approval_flow_id = self.env["utilities.approval.flow"].search(
            [("model_name", "=", self._name)], limit=1
        )
        return approval_flow_id

    def is_at_this_approval_level(self, group_xml_id):
        module = "utilities"
        module_group_xml_id = f"{module}.{group_xml_id}"

        group = self.env.ref(module_group_xml_id, raise_if_not_found=False)
        current_group = self._get_current_group_id()

        return current_group == group.id

    def is_second_time_level(self):
        return "-s" in self.approval_status

    def _get_user_group(self, group_xml_id):
        module = "utilities"
        module_group_xml_id = f"{module}.{group_xml_id}"
        group = self.env.ref(module_group_xml_id, raise_if_not_found=False)
        return group

    def _set_defaul_approval_flow(self, approval_flow_id):
        self.ensure_one()

        self.approval_flow_id = approval_flow_id

    def _is_next_level_last_level(self):
        self.ensure_one()
        current_group_id = self._get_current_group_id()
        selection = self._approval_flow_selection()
        before_last_level = selection[-2]
        before_last_level_value = before_last_level[0]

        if "-s" in before_last_level_value:
            before_last_level_value = before_last_level_value.split("-")[0]

        if current_group_id == int(before_last_level_value):
            return True
        else:
            return False

    def _off_approval(self):
        self.is_off_approval = True

    def _on_approval(self):
        self.is_off_approval = False

    def _approval_selection_value_array(self):
        approval_flow_id = self._get_approval_flow_id()
        level_ids = approval_flow_id.approval_level_ids

        return [self.get_section_value(level) for level in level_ids]

    def _approval_greater_than_this_group_id(self, group_id):
        if not self.approval_status:
            return False

        group_id_array = self._approval_selection_value_array()
        state_index = group_id_array.index(str(group_id))

        current_state_index = group_id_array.index(self.approval_status)

        if self._is_approved() or self._is_rejected():
            return True
        elif current_state_index > state_index:
            return True
        else:
            return False

    def get_group_id_by_xml_id(self, xml_group_id, is_second=False):
        group = self.env.ref(xml_group_id, raise_if_not_found=False)

        if group:
            if is_second:
                return f"{group.id}-s"
            else:
                return group.id
        else:
            return False

    def _get_supplier_group_id(self):
        xml_id = "utilities.group_ship_supplier"
        supplier_id = self.get_group_id_by_xml_id(xml_id)

        return supplier_id

    def _restart_approval_flow(self):
        group_id_array = self._approval_selection_value_array()
        if group_id_array:
            self.sudo_field().approval_status = group_id_array[0]

    def _propose_approval_to(self, xml_id, is_second=False):
        completed_xml_id = f"utilities.{xml_id}"

        group_id = self.get_group_id_by_xml_id(completed_xml_id, is_second)

        if group_id:
            self.sudo_field().approval_status = str(group_id)

    def get_approval_status(self):
        records = self.search([])

        for record in records:
            if record.request_state == CONST.APPROVED:
                record.sudo_field().approval_status = CONST.APPROVED
            elif record.request_state == CONST.REJECTED:
                record.sudo_field().approval_status = CONST.REJECTED
