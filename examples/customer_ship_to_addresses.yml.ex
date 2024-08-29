---
- hosts: all

  pre_tasks:
    - include_vars: ../vars/credentials.yml

  tasks:
    - name: Set Playbook Facts
      set_fact:
        auth_state_file: state.json

    - name: Login to QAD
      aux_auth:
        state: present
        qad_server: "{{ aux.hostname }}"
        state_file: "{{ auth_state_file }}"
        username: "{{ aux.username }}"
        password: "{{ aux.password }}"
          
    - name: Create new customer
      aux_customers:
        state: present
        qad_server: "{{ aux.hostname }}"
        headless: True
        state_file: "{{ auth_state_file }}"
        input_fields:
          main:
            customer_code: 1BRA009
            address:
              business_relation_name: Brads Customer
              address_search_name: Brads Customer
              city: Sydney
            accounting_profile:
              invoice_control_gl_profile_code: 10101-CRPAUS-A
              credit_note_control_gl_profile_code: 10101-CRPAUS-A
              pre_payment_control_gl_profile_code: 10101-CRPAUS-A
              sales_account_gl_profile_code: 20202-CRPAUS-SA
            payment:
              credit_terms_code: AP01
              invoice_status_code: AP-INITIAL
            tax:
              tax_zone: 10
      register: customer_created

    - name: Create new customer ship-to
      aux_customer_ship_to_addresses:
        state: present
        qad_server: "{{ aux.hostname }}"
        state_file: "{{ auth_state_file }}"
        headless: True
        input_fields:
          main:
            customer_code: 1BRA009
            customer_ship_to_name: Brad Liquor Store
          address:
            address_search_name: Brad Liquor Store
            city: Sydney
            country_code: AUS
          tax:
            tax_zone: 10
      register: customer_ship_to_created

    - name: Edit customer ship_to city
      aux_customer_ship_to_addresses:
        state: present
        qad_server: "{{ aux.hostname }}"
        state_file: "{{ auth_state_file }}"
        input_fields:
          main:
            customer_code: 1BRA009
            customer_ship_to_name: Brad Liquor Store
          address:
            address_search_name: Brad Liquor Store
            city: Sydney
            country_code: AUS
          tax:
            tax_zone: 10
      register: customer_ship_to_edited
  
    - name: Try to edit customer ship-to city again to same value
      aux_customer_ship_to_addresses:
        state: present
        qad_server: "{{ aux.hostname }}"
        state_file: "{{ auth_state_file }}"
        input_fields:
          main:
            customer_code: 1BRA009
            customer_ship_to_name: Brad Liquor Store
          address:
            address_search_name: Brad Liquor Store
            city: Sydney
            country_code: AUS
          tax:
            tax_zone: 10
      register: customer_ship_to_edited_again
  
    - name: Delete customer ship-to address
      aux_customer_ship_to_addresses:
        state: absent
        qad_server: "{{ aux.hostname }}"
        state_file: "{{ auth_state_file }}"
        input_fields:
          main:
            customer_code: 1BRA009
            customer_ship_to_name: Brad Liquor Store
      register: customer_ship_to_deleted

    - name: Delete customer ship-to address again
      aux_customer_ship_to_addresses:
        state: absent
        qad_server: "{{ aux.hostname }}"
        state_file: "{{ auth_state_file }}"
        input_fields:
          main:
            customer_code: 1BRA009
            customer_ship_to_name: Brad Liquor Store
      register: customer_ship_to_deleted_again

    - name: Delete customer 
      aux_customers:
        state: absent
        qad_server: "{{ aux.hostname }}"
        state_file: "{{ auth_state_file }}"
        input_fields:
          main:
            customer_code: 1BRA009
      register: customer_deleted
    
    - name: Logout
      aux_auth:
        state: absent
        qad_server: "{{ aux.hostname }}"
        state_file: "{{ auth_state_file }}"

    - name: Assert all tasks
      assert:
        that:
          - customer_created.changed == True
          - customer_ship_to_created.changed == True
          - customer_ship_to_edited.changed == True
          - customer_ship_to_edited_again.changed == False
          - customer_ship_to_deleted.changed == True
          - customer_ship_to_deleted_again.changed == False
          - customer_deleted.changed == True

