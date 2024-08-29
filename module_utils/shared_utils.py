import time

from playwright.sync_api._generated import Locator, Page


# Copilot prompt: function to traverse nested dictionary tree and return dict with all keys converted to camel case
def convert_dict_to_camel_case(input_fields: dict, case_sensitive_words: list[str] = []) -> dict:
    """Convert all keys in nested dictionary to camel case"""
    camel_dict = {}
    for key, val in input_fields.items():
        if isinstance(val, dict):
            val = convert_dict_to_camel_case(val, case_sensitive_words)
        elif isinstance(val, list):
            conv_list = []
            for item in val:
                conv_list.append(convert_dict_to_camel_case(item, case_sensitive_words))
            val = conv_list
        camel_dict[to_camel_case(key, case_sensitive_words)] = val
    return camel_dict


def to_camel_case(snake_case: str, case_sensitive_words: list[str] = []) -> str:
    """Convert snake case ansible arg to camel case for html locator"""
    words = snake_case.split("_")
    # First word is lowercase
    camel_string = words[0].lower()

    # Loop through remaining words
    for word in words[1:]:
        if len(case_sensitive_words) != 0:
            # Some words need to be case sensitive, this handles that
            for case_sensitive_word in case_sensitive_words:
                if word.lower() == case_sensitive_word.lower():
                    word = case_sensitive_word
                else:
                    word = word.title()
        else:
            word = word.title()

        camel_string += word
    return camel_string


def change_input_fields(page: Page, input_fields: dict, changed: bool = False) -> bool:
    """
    recursively update any input fields, returns true
    if any are changed
    """
    for key, val in input_fields.items():
        if isinstance(val, dict):
            changed = change_input_fields(page, val, changed)
        elif isinstance(val, list):
            # this is a table, the table id naming is not consistent
            # so we have hardcoded handling in the module XXX:todo
            continue
        else:
            html_locator = f"[name={key}]"
            result = string_field(page, html_locator, str(val))
            if result == "changed":
                changed = True
    return changed


def check_input_fields(page: Page, input_fields: dict, incorrect_object_details: list = []) -> list[str]:
    """
    recursively check values in input fields, returns list of incorrect details if found
    """
    for key, val in input_fields.items():
        if isinstance(val, dict):
            incorrect_object_details = list(set(incorrect_object_details + check_input_fields(page, val, incorrect_object_details)))
        elif isinstance(val, list):
            # we need to manually handle this in the library module
            # due to inconsistent table naming XXX:todo
            continue
        else:
            locator = f"[name={key}]"
            field = page.locator(locator)
            if field.input_value() != str(val):
                incorrect_object_details.append(key)
    return incorrect_object_details


def check_input_rows(page: Page, table_id_string: str, input_fields: list[dict]) -> list[dict]:
    """
    given a list of dicts as rows, check if rows in table match
    returns ansible defined row items that don't match in page rows
    """
    table_locator = page.locator("[id=%s]" % table_id_string)
    input_table_check = input_fields.copy()
    if table_locator.is_visible():
        outer_table = page.locator(
            "#%s > .panel-body > table > tbody > tr > td" % table_id_string).first
        inner_table = outer_table.locator(
            ".k-grid > .k-grid-content > table")
        rows = inner_table.locator("tbody tr")
        if len(rows.all()) == len(input_fields):
            # if row numbers don't match, we can bypass this check
            for row in rows.all():
                for row_details in input_fields:
                    row_details_check = row_details.copy()
                    for key, val in row_details.items():
                        if val == row.locator(".qFieldName-%s" % key).text_content():
                            row_details_check.pop(key)
                    if len(row_details_check) == 0:
                        # row matched, remove it from our input_table_check
                        input_table_check.remove(row_details)
        return input_table_check
    else:
        raise Exception


def check_object_details(page: Page, module_details: dict[str, str]) -> list[str]:
    incorrect_object_details = []
    for key, val in module_details.items():
        locator = f"[name={key}]"

        field = page.locator(locator)
        if field.input_value() != val:
            incorrect_object_details.append(key)

    return incorrect_object_details


def quicksearch_for_object(page: Page, object_code: str) -> Locator:
    """
        Search browse using quicksearch bar,
        return the object playwright locator if exists
    """
    # Use browse search bar to search for object
    searchbar_locator = page.locator("[id=tbQuickSearch_BrowseDataGrid]")
    # delete any default view options, we want a clean search bar
    def_view_options = searchbar_locator.locator("..").get_by_title("delete").all()
    for view_option in def_view_options:
        if view_option.is_visible():
            view_option.click()

    if searchbar_locator.is_visible():
        searchbar_locator.fill(object_code, timeout=15000)

    page.locator("[id=btnBrowseSearch]").click()

    # Wait for loading spinner to detatch
    page.locator(".k-loading-color").first.wait_for(state="detached")
    # Find first element in results table
    object_locator = page.locator(
        "#qGridContent > table[aria-activedescendant=kGrid_BrowseDataGrid_active_cell] > tbody > tr"
    ).first
    return object_locator


def advsearch_for_object(page: Page, filter_defs: list[dict[str, str, str]]) -> Locator:
    """
        Search browse using advanced search options,
        return the object playwright locator if exists
    """
    # open the advanced search caret
    page.locator("[id=btnSearchAdvance]").click()
    # clear all previous searches
    page.locator("[id=btnSearchClearAll]").click()

    # Remove all filters (aside from last one that is required to be there)
    while (xremove := page.locator("[id=btnRemoveSearchCond]").first).is_enabled():
        xremove.click()

    # populate/add filter item rows
    filter_table = page.locator(
        "#browseAdvanceSearchPopup > .qAdvanceSearchContainer > table"
    ).first

    filter_defs_index = 1
    for filter_def in filter_defs:
        # find the empty row, sometimes it's added above, sometimes below
        row_index = 0
        rows = filter_table.locator("tbody > tr").all()
        for row in rows:
            field_select, operator_select, value_input = row.locator("td").all()[:3]
            if value_input.get_by_role("textbox").count() == 1:
                prefill = value_input.get_by_role("textbox").input_value()
            else:
                prefill = value_input.get_by_role("option").input_value()
            if prefill == "":
                break
            row_index += 1
        # Select Field list option (sometimes there are multiples)
        field_select.get_by_role("button").click()
        field_select_list = page.locator(
                "li > span.k-list-item-text",
                has=page.get_by_text(filter_def["field"], exact=True)
            ).all()
        for field_list_item in field_select_list:
            if field_list_item.is_visible():
                field_list_item.click()
                break
        # Select Operator
        operator_select.get_by_role("button").click()
        page.locator(
            "li > span.k-list-item-text",
            has=page.get_by_text(filter_def["operator"], exact=True)
        ).last.click(timeout=5000)

        # Select/Input value
        if value_input.get_by_role("textbox").count() == 1:
            # if it needs text input
            value_input.get_by_role("textbox").fill(filter_def["value"])
        else:
            # if it's a drop down selector
            value_input.get_by_role("button").first.click()
            # there is some ugliness here, this element requires .first
            # as oppoosed to all the other elements above... unknown reason
            page.locator(
                "li > span.k-list-item-text",
                has=page.get_by_text(filter_def["value"], exact=True)
            ).first.click(timeout=5000)

        if len(filter_defs) > filter_defs_index:
            # click the + button to add another filter condition
            row.locator("#btnAddSearchCond").click(timeout=5000)
            filter_defs_index += 1

    page.locator("[id=btnSaveSearchCond]").click()
    # Wait for loading spinner to detatch
    page.locator(".k-loading-color").first.wait_for(state="detached")
    # Find first element in results table
    object_locator = page.locator(
        "#qGridContent > table[aria-activedescendant=kGrid_BrowseDataGrid_active_cell] > tbody > tr"
    ).first
    return object_locator


def string_field(page: Page, locator_string: str, text: str) -> str:
    """Idempotently update given field in object edit page"""
    input_field = page.locator(locator_string)
    if input_field.input_value() == text:
        return "ok"

    if input_field.is_hidden():
        # find the parent, and click it
        parent_input_field = input_field.locator("..")
        parent_input_field.click()
        select_list_field = parent_input_field.get_by_role("listbox")
        if select_list_field != None:
            field_select_list = select_list_field.locator(
                    "li > span.k-list-item-text",
                    has=page.get_by_text(text, exact=True)
                    ).all()
            for field_list_item in field_select_list:
                if field_list_item.is_visible():
                    field_list_item.click()
            return "changed"
    input_field.clear()
    input_field.fill(text)
    return "changed"


def add_table_rows(page: Page, table_id_string: str, input_fields: list) -> str:
    """
       given a list of row input values (as a dict per row),
       create new rows in a table in a maintenance page
    """
    table_locator = page.locator("[id=%s]" % table_id_string)
    if table_locator.is_visible():
        outer_table = page.locator(
            "#%s > .panel-body > table > tbody > tr > td" % table_id_string).first
        inner_table = outer_table.locator(
            ".k-grid > .k-grid-toolbar > #qGridToolbar")
        for item in input_fields:
            inner_table.get_by_text("New").first.click()
            # this is required for the fields to be ready for input
            time.sleep(2)
            change_input_fields(table_locator, item)
    changed = True
    return changed


def remove_table_rows(page: Page, table_id_string: str) -> bool:
    """
       given a table id, remove all existing rows
    """
    changed = False
    table_locator = page.locator("[id=%s]" % table_id_string)
    if table_locator.is_visible():
        outer_table = page.locator(
            "#%s > .panel-body > table > tbody > tr > td" % table_id_string).first
        inner_table = outer_table.locator(
            ".k-grid > .k-grid-content > table")
        while len(inner_table.locator("tbody tr").all()) > 0:
            row = inner_table.locator("tbody tr").first
            row.locator("td").nth(1).click()
            table_locator.get_by_role("button").filter(has_text="Delete").click()
            popup_locator = page.locator("#qModalDialogConfirm")
            popup_locator.wait_for()
            popup_locator.click()
            changed = True
    return changed
