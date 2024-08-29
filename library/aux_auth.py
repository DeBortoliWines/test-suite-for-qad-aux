#!/usr/bin/python

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function

import os

from ansible.module_utils.basic import AnsibleModule
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

__metaclass__ = type

DOCUMENTATION = r"""
---
module: aux_auth

short_description: Manage authentication of QAD AUX instance
description: This module idempotently manages the authentication state of a qad aux instance 

options:
    state_file:
        description: Authentication state file path to check/set auth cookies
        required: true
        type: str
    state:
        description: Authentication state to set
        required: true
        type: str
        choices: present, absent
    qad_server:
        description: QAD server name to manage authentication for
        required: true
        type: str
    headless:
        description: run playwright browser in headless mode
        required: false
        type: bool
        default: True
    username:
        description: Authentication username
        required: false
        type: str
    password:
        description: Authentication password
        required: false
        type: str

author:
    - Joel Giovinazzo (joel_giovinazzo@debortoli.com.au)
"""

EXAMPLES = r"""
# Log in to QAD instance with visible browser window
- name: Login to qad-test
  my_namespace.my_collection.qad_auth:
    state_file: state.json
    qad_server: qad-test
    headless: False
    username: my_username
    password: my_password
    state: present

# Log out of QAD instance
- name: Log  out of qad-test
  my_namespace.my_collection.qad_auth:
    state_file: state.json
    qad_server: qad-test
    state: absent
"""

RETURN = r"""
# These are examples of possible return values, and in general should use other names for return values.
message:
    description: Output status message
    type: str
    returned: always
    sample: 'Logged in as my_username'
"""


def run_module():
    # Define available arguments/parameters a user can pass to the module
    module_args = dict(
        state_file=dict(type="str", required=True),
        state=dict(type="str", required=True, choices=["present", "absent"]),
        qad_server=dict(type="str", required=True),
        headless=dict(type="bool", required=False, default=True),
        username=dict(type="str"),
        password=dict(type="str"),
    )

    # Define response object
    result = dict(changed=False, message="")

    # Initiate ansible object
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_together=[("username", "password")],
    )

    if module.check_mode:
        module.exit_json(**result)

    # Check if state file exists
    state_file_exists = os.path.exists(module.params["state_file"])

    playwright = sync_playwright().start()
    timeout = 10

    # Initiate browser
    browser = playwright.chromium.launch(headless=module.params["headless"])
    # Initiate page differently depending on existance of state file
    if not state_file_exists:
        page = browser.new_page()
    else:
        context = browser.new_context(
            storage_state=module.params["state_file"])
        page = context.new_page()

    # If we want to be logged in
    if module.params["state"] == "present":
        # Check if state file has been passed through
        home_url = f"http://{module.params['qad_server']}:22010/qad-central/#/view/webshell/home"
        page_response = page.goto(home_url)

        # If we get to the home page, we can assume we are logged in.
        if page_response is not None and "login.jsp" not in page_response.url:
            result["message"] = "Already logged in - sent to home screen"
            module.exit_json(**result)

        # Here we should be at the login screen
        page.locator("[name=username]").fill(module.params["username"])
        page.locator("[name=password]").fill(module.params["password"])
        page.locator("[id=logInBtn]").click()
        try:
            page.wait_for_url("**/qad-central/#/view/webshell/home",
                              timeout=timeout * 1000)
        except PlaywrightTimeoutError:
            result["message"] = "Error: Timeout Error"
            module.fail_json(
                msg=
                f"QAD Took too long to load after logging in (> {timeout}s)",
                **result,
            )
        context = browser.contexts[0]
        context.storage_state(path=module.params["state_file"])

        result["message"] = f"logged in as user {module.params['username']}"
        result["changed"] = True
        module.exit_json(**result)

    # If we want to be logged out
    else:
        page.goto(
            f"http://{module.params['qad_server']}:22010/qad-central/#/view/webshell/home"
        )
        try:
            page.wait_for_url(
                "**/qad-central/resources/login.jsp*",
                timeout=1 * 1000,
            )
            result["message"] = "Already logged out - Sent to login screen"
            module.exit_json(**result)
        except PlaywrightTimeoutError:
            page.locator("[id=kMenuUserInfo_wrapper]").click()
            page.locator("[data-id=logoutMenuItem]").click()
            if state_file_exists:
                os.remove(module.params["state_file"])
            result["message"] = "Logged out of QAD"
            result["changed"] = True
            module.exit_json(**result)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
