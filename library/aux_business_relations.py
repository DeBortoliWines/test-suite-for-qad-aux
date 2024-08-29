#!/usr/bin/python

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function

import os

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.shared_utils import (check_input_fields,
                                               quicksearch_for_object,
                                               convert_dict_to_camel_case,
                                               change_input_fields)
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import expect, sync_playwright

__metaclass__ = type

DOCUMENTATION = r"""
---
module: aux_business_relations

short_description: Manage Business Relations in QAD AUX instance
description: This module idempotently manages Business Relations state in a qad aux instance

options:
    state:
        description: Business Relation state state to set
        required: true
        type: str
        choices: present, absent
    state_file:
        description: Authentication state file path to check auth cookies
        required: true
        type: str
    qad_server:
        description: QAD server name to manage business relation for
        required: true
        type: str
    headless:
        description: run playwright browser in headless mode
        required: false
        type: bool
        default: True
    input_fields:
        description: dictionary of input fields available on a maintenance screen, identified by their css "name" attribute
        required: false
        type: dict
        main:
            description: dictionary of input fields under the Main section heading
            required: false
            type: dict
                business_relation_code:
                    description: QAD business relation code to manage
                    required: true
                    type: str
                business_relation_name1:
                    description: QAD business relation name
                    required: false
                    type: str
                business_relation_search_name:
                    description: QAD business relation search name
                    required: true
                    type: str
                addresses:
                    description: dictionary of input fields under the Addresses section heading
                    required: false
                    type: dict
                        head_office:
                            description: dictionary of input fields under the Head Office section heading
                            required: false
                            type: dict
                                head_office_street1:
                                    description: Address 1
                                    required: false
                                    type: str
                                head_office_street2:
                                    description: Address 2
                                    required: false
                                    type: str
                                head_office_street3:
                                    description: Address 3
                                    required: false
                                    type: str
                                head_office_zip_code:
                                    description: Postal Code
                                    required: false
                                    type: str
                                head_office_city:
                                    description: City
                                    required: true
                                    type: str
                                head_office_state_code:
                                    description: State
                                    required: false
                                    type: str
                                head_office_telephone:
                                    description: Phone 1
                                    required: false
                                    type: str
                                head_office_fax:
                                    description: Phone 2
                                    required: false
                                    type: str
                                head_office_email:
                                    description: Email
                                    required: false
                                    type: str
                                head_office_web_site:
                                    description: Website
                                    required: false
                                    type: str


author:
    - Bernard Gray (bernard_gray@debortoli.com.au)
"""

EXAMPLES = r"""
# Create/Edit a business relation with a visible browser window
- name: Create new Business Relation
  aux_business_relation:
    state: present
    qad_server: qad-test
    headless: False
    state_file: state.json
    input_fields:
      main:
        business_relation_code: 70-522
        business_relation_name1: Bernard Gray
        business_relation_search_name: Bernard Gray
        addresses:
          head_office:
            head_office_street1: 1 Ansible Way
            head_office_street2:
            head_office_street3:
            head_office_zip_code: 2000
            head_office_city: Sydney
            head_office_state_code: NSW
            head_office_telephone: 02 9999 0100
            head_office_fax:
            head_office_email: ansible@qad.fakedomain
            head_office_web_site: https://ansible.com

- name: Delete Business Relation
  aux_business_relation:
    state: absent
    qad_server: qad-test
    state_file: state.json
    input_fields:
      main:
        business_relation_code: 70-522
"""

RETURN = r"""
# These are examples of possible return values, and in general should use other names for return values.
message:
    description: Output status message
    type: str
    returned: always
    sample: 'Business Relation created successfully'
"""


def run_module():
    # Define available arguments/parameters a user can pass to the module
    module_args = dict(
        state_file=dict(type="str", required=True),
        state=dict(type="str", required=True, choices=["present", "absent"]),
        qad_server=dict(type="str", required=True),
        headless=dict(type="bool", required=False, default=True),
        input_fields=dict(
            required=False,
            type="dict",
            main=dict(
                required=False,
                type="dict",
                options=dict(
                    business_relation_code=dict(type="str", required=True),
                    business_relation_name1=dict(type="str", required=False),
                    business_relation_search_name=dict(type="str", required=True),
                    addresses=dict(
                        required=False,
                        type="dict",
                        options=dict(
                            head_office=dict(
                                required=False,
                                type="dict",
                                options=dict(
                                    head_office_street1=dict(type="str", required=False),
                                    head_office_street2=dict(type="str", required=False),
                                    head_office_street3=dict(type="str", required=False),
                                    head_office_zip_code=dict(type="str", required=False),
                                    head_office_city=dict(type="str", required=True),
                                    head_office_state_code=dict(type="str", required=False),
                                    head_office_telephone=dict(type="str", required=False),
                                    head_office_fax=dict(type="str", required=False),
                                    head_office_email=dict(type="str", required=False),
                                    head_office_web_site=dict(type="str", required=False),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        ),
    )

    # Define response object
    result = dict(changed=False, message="")

    # Initiate ansible object
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            (
                "state",
                "present",
                ["input_fields"],
            )
        ],
    )

    if module.check_mode:
        module.exit_json(**result)

    # common variables
    # define url we need to access
    item_url = f"http://{module.params['qad_server']}:22010/qad-central/#/view/qraview/hybridbrowse?viewMetaUri=urn:view:meta:com.qad.erp.base.businessRelationV2s"
    # define name of this page
    item_type = "Business Relation"
    # define primary search key
    item_search_key = "business_relation_code"

    # Check if state file exists
    state_file_exists = os.path.exists(module.params["state_file"])
    if not state_file_exists:
        module.fail_json(msg="Authentication state file does not exist!", **result)

    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=module.params["headless"])
    context = browser.new_context(storage_state=module.params["state_file"])
    page = context.new_page()
    page.goto(item_url)

    # If we are sent to the login screen we are not logged in
    try:
        page.wait_for_url(
            "**/qad-central/resources/login.jsp*",
            timeout=1 * 1000,
        )
        module.fail_json(msg="No current logged in user", **result)
    except PlaywrightTimeoutError:
        pass

    # If we want to create/maintain
    if module.params["state"] == "present":
        # First we check if item already exists
        item_locator = quicksearch_for_object(page, module.params["input_fields"]["main"][item_search_key])
        if item_locator.is_visible():
            item_locator.click(click_count=2)
        else:
            # Create New Item
            page.locator("[id=ToolBtnNew]").click()

        page.locator(".k-loading-color").first.wait_for(state="detached")

        # Construct all Item details with camel case keys
        args = convert_dict_to_camel_case(module.params["input_fields"], ["GL","EMail"])

        # Enter details in mapped fields
        result["changed"] = change_input_fields(page, args)

        if result["changed"]:
            result["message"] = f"{item_type} has been updated"
            page.locator("[id=ToolBtnSave]").click()

            # Wait for success toast to appear
            toast = page.locator(".toast-message").first
            toast.wait_for(timeout=160000)
            try:
                expect(toast).to_have_text("saved", ignore_case=True)
            except (PlaywrightTimeoutError, AssertionError):
                module.fail_json(msg=f"Error saving {item_type}")

            # Exit item menu and search for item again, confirm it exists
            page.locator("#btnViewFormPane").click()
            if not quicksearch_for_object(
                page, module.params["input_fields"]["main"][item_search_key]
            ).is_visible():
                module.fail_json(msg=f"{item_type} not found after saving")

            # Check that all fields have been updated correctly
            item_locator.click(click_count=2)
            page.locator(".k-loading-color").first.wait_for(state="detached")
            incorrect_fields = check_input_fields(page, args)
            if incorrect_fields:
                module.fail_json(
                    msg=f"{item_type} details have not correctly been updated {str(incorrect_fields)}"
                )

    elif module.params["state"] == "absent":
        # Find item
        item_locator = quicksearch_for_object(page, module.params["input_fields"]["main"][item_search_key])
        if not item_locator.is_visible():
            result["message"] = f"{item_type} does not exist"
            module.exit_json(**result)
        item_locator.click(click_count=2)

        # Delete Item
        page.locator("#ToolBtnDelete").click()
        popup_locator = page.locator("#qModalDialogConfirm")
        popup_locator.wait_for()
        popup_locator.click()

        # Wait for deleted toast message
        toast = page.locator(".toast-message").first
        toast.wait_for()
        try:
            expect(toast).to_have_text("deleted", ignore_case=True)
        except (PlaywrightTimeoutError, AssertionError):
            module.fail_json(msg=f"Error deleting {item_type}")

        # Check if item no longer exists in browse
        page.locator("#btnViewFormPane").click()
        if quicksearch_for_object(page, module.params["input_fields"]["main"][item_search_key]).is_visible():
            module.fail_json(msg=f"Could not delete {item_type}")

        result["message"] = f"{item_type} has been deleted"
        result["changed"] = True
    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
