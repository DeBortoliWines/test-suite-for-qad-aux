# QAD AUX Ansible Test Suite

This is a series of [Ansible](https://www.ansible.com/how-ansible-works/) Modules for testing/interacting with the [QAD AUX](https://www.qad.com/solutions/adaptive-ux) Manufacturing ERP system.

Tests are built as an [Ansible Playbook](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_intro.html), some examples are included to assist getting started.

## Status

**Very early development** - Not all fields for all modules are supported (but all mandatory fields are). Many things are subject to change without warning - please get in touch with me if you are using this in any serious capacity.

Assistance to add non-mandatory fields to existing modules, as well as the development of new modules is very welcome!

## Introduction

[QAD AUX](https://www.qad.com/solutions/adaptive-ux) is a web based iteration of QAD's Enterprise Resource Planning (ERP) system 

[Ansible](https://www.ansible.com/how-ansible-works/) is an open source, command-line IT automation software application written in Python.

[Playwright](https://playwright.dev/) is an open-source automation library for browser testing and web scraping.

This project combines the simple task-based nature of Ansible config automation, with the automated web navigation/testing capabilities of Playwright to create a simple and flexible testing environment for QAD AUX.

## Demo

[![Screenshot of the QAD AUX frontend testing tool in progress](https://img.youtube.com/vi/_s2ovk1pIYA/0.jpg)](https://www.youtube.com/watch?v=_s2ovk1pIYA)

## Setup for Development (Linux)

1. Clone this repo
    
2. Install pip according to your preferred Linux distro method
    
3. Export proxies (if required):

    ```
    export http_proxy={{ proxy }}:{{ port }}
    export https_proxy={{ proxy }}:{{ port }}
    ```
4. Install dependencies
    
    ```
    pip install -r requirements.txt
    ```
5. Fix path to pip binaries
    
    ```
    PATH=${PATH}:~/.local/bin
    ```
6. Install browser binaries for playwright
    
    ```
    playwright install
    ```
7. Copy `vars/credentials.yml.ex`
    
    ```
    cp vars/credentials.yml.ex vars/credentials.yml
    ```
8. Edit `vars/credentials.yml` to contain your username/password details
    
9. Initial testing with the `aux_auth` module

```
ansible-playbook --connection=local -i localhost, examples/auth.yml.ex
```

## Repository Layout

 - `examples/*.yml.ex`: Example test suites in ansible playbook formats, to demonstrate testing for different `library/` modules
 - `library/`: A set of custom ansible modules, designed to test different modules of the QAD ERP
 - `module_utils/`: Custom shared python libraries, functions and scripts
 - `playbooks/`: (not created in this repo) For internal test development and maintenance

## Creating Testing Playbooks for Internal Use

Create a `playbooks/` directory. This directory is ignored by `.gitignore`, therefore it can contain it's own git repository for local development and version control. This is where internal playbook development is intended to occur.

Supported QAD AUX modules are contained in the `library/` directory. For info on how to use these modules, explore the playbook examples in the `examples/` directory.

You can copy and paste the example playbooks (with rename) to your custom `playbooks/` directory, and begin building custom playbooks.

> **Note:** For some modules, company sensitive information is required to be stored in the playbooks - for this reason, all `.yml` file extensions are also in `.gitignore`, to lower the risk of accidentally committing anything to a public repository.

## Notes for Developing Custom Library Modules

**Module Naming:** Each `library/` module is named according to it's Maintenance Page name, eg the **Suppliers** maintenance screen in AUX, is represented in the Ansible modules as aux_suppliers.py

> **Note:** To date, no work has been done to develop for AUX Browse or Report screens (which sometimes share the name of the Maintenance Screen) so no standard has been developed to handle that (yet).

Work has been done to make the module development templated where possible. In general, adding support for a new module looks like:
 - copy an existing module of similar complexity to your new module name in the `library/` directory, observing the **naming convention**
 - (optionally) copy the corresponding test `*.yml.ex` module into your `playbooks/` directory (internal naming convention may apply)
 - open the AUX maintenance screen on your QAD AUX server, open the developer tools pane and focus the `Elements` tab
 - identify the mandatory field html `name` attributes (and optionally, the non-mandatory fields) in **camelCase** format, and their section hierarchy
 - update the new `library/` module with:
   - the QAD AUX URL suffix in the `item_url` variable
   - the QAD maintenance screen name in the `item_type` variable
   - identify the primary AUX Quicksearch key from the html `name` attributes, and update the `item_search_key` variable
 - update the test playbook (if created) with the new module name, and list of mandatory html `name` attributes converted to **snake_case** format
 - update the new `library/` module `module_args` variable with the list of html `name` attributes converted to **snake_case** format

In general, this will be enough to function. The majority of the heavy lifting occurs in the module with these two function calls:
```python
...
         # Construct all html element details as camel case keys
        args = convert_dict_to_camel_case(module.params["input_fields"], ["GL"])

        # Enter details in mapped fields
        result["changed"] = change_input_fields(page, args)
...
```

... however, there are some **exceptions**:

1. Some html `name` attributes do not translate cleanly to snake_case format. Eg `invoice_control_gl_profile_code` => `invoiceControlGLProfileCode` where `GL` requires full capitalisation. Exceptions like this can be correctly cased as an argument to `convert_dict_to_camel_case`

2. Tables in maintenance screens - for example, there is a `BankingPanel` in the Suppliers maintenance screen. These tables are not named consistently, and require some bespoke identification and handling outside of the `change_input_fields()` function. Check the `library/aux_suppliers.py` module for an example of how to handle this case.

**Documentation:** Lastly, update the documentation headers in the module to match the snake_case variables in the playbooks, and add any examples.

## Not Yet Done

- Capture return values from QAD workflows as Ansible variables for reuse, eg create a new Purchase Order, capture the new Purchase Order number as an Ansible variable for use in later tasks such as Receipting 
- Test Browses and Reports
- Many many maintenance screens
- [Generate online documentation from the module header docs](https://stackoverflow.com/questions/65735013/how-to-generate-a-documentation-from-ansible-modules)
