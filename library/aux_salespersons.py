#!/usr/bin/python

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function

import os
import sys

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
module: aux_salespersons

short_description: Manage Salespersons in QAD AUX instance
description: This module idempotently manages salesperson state in a qad aux instance

options:
    state:
        description: salesperson state to set
        required: true
        type: str
        choices: present, absent
    state_file:
        description: Authentication state file path to check auth cookies
        required: true
        type: str
    qad_server:
        description: QAD server name to manage salespersons for
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
                salesperson_code:
                    description: QAD salesperson code to manage
                    required: true
                    type: str
                business_relation_code:
                    description: QAD business relation code to associate with salesperson
                    required: true
                    type: str
                sales_territory:
                    description: QAD business relation name
                    required: false
                    type: str


author:
    - Bernard Gray (bernard_gray@debortoli.com.au)
"""

EXAMPLES = r"""
# Create/Edit a salesperson with a visible browser window
- name: Create new Salesperson
    state: present
    qad_server: qad-test
    headless: True
    state_file: state.json
    input_fields:
      main:
        salesperson_code: 70-500
        sales_territory: 70
        business_relation_code: 70-500

- name: Delete salesperson
  aux_salespersons:
    state: absent
    qad_server: qad-test
    headless: True
    state_file: state.json
    input_fields:
      main:
        salesperson_code: 70-500
"""

RETURN = r"""
# These are examples of possible return values, and in general should use other names for return values.
message:
    description: Output status message
    type: str
    returned: always
    sample: 'Salesperson created successfully'
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
                    salesperson_code=dict(type="str", required=True),
                    business_relation_code=dict(type="str", required=True),
                    sales_territory=dict(type="str", required=False),
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
    item_url = f"http://{module.params['qad_server']}:22010/qad-central/#/view/qraview/hybridbrowse?viewMetaUri=urn:view:meta:com.qad.erp.sales.salespersons"
    # define name of this page
    item_type = "Salespersons"
    # define primary search key
    item_search_key = "salesperson_code"

    # Check if state file exists
    state_file_exists = os.path.exists(module.params["state_file"])
    if not state_file_exists:
        module.fail_json(msg="Authentication state file does not exist!", **result)

    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=module.params["headless"])
    context = browser.new_context(storage_state=module.params["state_file"])
    page = context.new_page()
    page.goto(
        item_url
    )

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
        args = convert_dict_to_camel_case(module.params["input_fields"], ["GL"])
        sys.stderr.write(str(args))

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
