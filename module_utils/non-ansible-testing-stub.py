#!/bin/python3

# this script is **very** rough, and intended to be a quick and dirty
# testing method without ansible in the mix.

# No guarantees of functionality, it's possible of value as a starting point

from __future__ import absolute_import, division, print_function

import os
import time

from shared_utils import (check_object_details,
                          quicksearch_for_object,
                          convert_dict_to_camel_case,
                          check_input_fields,
                          check_input_rows,
                          change_input_fields)
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import expect, sync_playwright


hostname = "hostname.domain"
port = "22010"
state_file = os.path.join("../", "playbooks", "state.json")
state_file_exists = os.path.exists(state_file)
if not state_file_exists:
    print(f"Authentication state file does not exist at: {state_file}")
    exit()

playwright = sync_playwright().start()
browser = playwright.chromium.launch(headless=False)
context = browser.new_context(storage_state=state_file)
page = context.new_page()
page.goto(
    f"https://{hostname}:{port}/qad-central/#/view/qraview/hybridbrowse?viewMetaUri=urn:view:meta:com.qad.erp.base.businessRelationV2s"
)

# If we are sent to the login screen we are not logged in
try:
    page.wait_for_url(
        "**/qad-central/resources/login.jsp*",
        timeout=1 * 1000,
    )
    print("No current logged in user")
    exit()
except PlaywrightTimeoutError:
    pass

module_params = dict(
    input_fields=dict(
        main=dict(
            business_relation_code="70-707",
            business_relation_name1_gl="John Doe",
            business_relation_search_name="John Doe",
            addresses=dict(
                head_office=dict(
                    head_office_street1="1 Waterloo Rd",
                    head_office_zip_code="2000",
                    head_office_city="Sydney",
                    head_office_state_code="NSW",
                    head_office_telephone="02 9999 0000",
                    head_office_email="ansible@qad.com",
                    head_office_website="https://www.qad.com",
                ),
            ),
        ),
    ),
)

business_relation_locator = quicksearch_for_object(page, module_params["input_fields"]["main"]["business_relation_code"])
if business_relation_locator.is_visible():
    business_relation_locator.click(click_count=2)
else:
    # Create New business_relation
    page.locator("[id=ToolBtnNew]").click()

args = convert_dict_to_camel_case(module_params["input_fields"], ["GL", "EMail"])
print(args)

time.sleep(5)
