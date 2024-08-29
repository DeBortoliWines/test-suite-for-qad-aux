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
          
    - name: make sure our Supplier doesn't exist from the start
      aux_suppliers:
        state: absent
        qad_server: "{{ aux.hostname }}"
        state_file: "{{ auth_state_file }}"
        input_fields:
          main:
            supplier_code: 5ST000
      changed_when: False

    - name: Create New Supplier
      aux_suppliers:
        state: present
        qad_server: "{{ aux.hostname }}"
        headless: True
        state_file: "{{ auth_state_file }}"
        input_fields:
          main:
            supplier_code: 5ST000
            address:
              business_relation_name: 3 Stop Driving School 
              address_search_name: Joes supplier
              city: Sydney
            accounting_profile:
              invoice_control_gl_profile_code: 10111-CRPAUS-A
              credit_note_control_gl_profile_code: 10111-CRPAUS-A
              pre_payment_control_gl_profile_code: 10111-CRPAUS-A
              purchase_account_gl_profile_code: 20202-CRPAUS-PA
            payment:
              credit_terms_code: AP07
              invoice_status_code: AP-INITIAL
          tax:
            tax_zone: 10
          banking:
            - bank_acc_format_code: "XX"
              bank_number_formatted: "55545556"
              own_bank_number: "98765432"
              bank_business_relation_code: "BNK"
              bank_number_branch: "063063"
              currency_code: "AUD"
            - bank_acc_format_code: "XX"
              bank_number_formatted: "44463377"
              own_bank_number: "98765432"
              bank_business_relation_code: "BNK"
              bank_number_branch: "666455"
              currency_code: "AUD"
      register: supplier_created

    - name: Modify Supplier to same name
      aux_suppliers:
        state: present
        qad_server: "{{ aux.hostname }}"
        state_file: "{{ auth_state_file }}"
        input_fields:
          main:
            supplier_code: 5ST000
            address: 
              business_relation_name: 3 Stop Driving School 
              address_search_name: Joes supplier
              city: Sydney
            accounting_profile:
              invoice_control_gl_profile_code: 10111-CRPAUS-A
              credit_note_control_gl_profile_code: 10111-CRPAUS-A
              pre_payment_control_gl_profile_code: 10111-CRPAUS-A
              purchase_account_gl_profile_code: 20202-CRPAUS-PA
            payment:
              credit_terms_code: AP07
              invoice_status_code: AP-INITIAL
          tax:
            tax_zone: 10
      register: supplier_not_modified

    - name: Modify Supplier business relation name
      aux_suppliers:
        state: present
        qad_server: "{{ aux.hostname }}"
        state_file: "{{ auth_state_file }}"
        input_fields:
          main:
            supplier_code: 5ST000
            address:
              business_relation_name: PLEASE Stop Driving School 
      register: supplier_edited

    - name: Modify Supplier business relation name again
      aux_suppliers:
        state: present
        qad_server: "{{ aux.hostname }}"
        state_file: "{{ auth_state_file }}"
        input_fields:
          main:
            supplier_code: 5ST000
            address:
              business_relation_name: PLEASE Stop Driving School 
      register: supplier_edited_again

    - name: Modify Banking rows
      aux_suppliers:
        state: present
        headless: True
        qad_server: "{{ aux.hostname }}"
        state_file: "{{ auth_state_file }}"
        input_fields:
          main:
            supplier_code: 5ST000
            address:
              business_relation_name: PLEASE Stop Driving School 
          banking:
            - bank_acc_format_code: "XX"
              bank_number_formatted: "99999999"
              own_bank_number: "98765432"
              bank_business_relation_code: "BNK"
              bank_number_branch: "063063"
              currency_code: "AUD"
            - bank_acc_format_code: "XX"
              bank_number_formatted: "44463377"
              own_bank_number: "98765432"
              bank_business_relation_code: "BNK"
              bank_number_branch: "666455"
      register: supplier_banking_edited

    - name: Modify Banking rows to same value again
      aux_suppliers:
        state: present
        headless: True
        qad_server: "{{ aux.hostname }}"
        state_file: "{{ auth_state_file }}"
        input_fields:
          main:
            supplier_code: 5ST000
            address:
              business_relation_name: PLEASE Stop Driving School 
          banking:
            - bank_acc_format_code: "XX"
              bank_number_formatted: "99999999"
              own_bank_number: "98765432"
              bank_business_relation_code: "BNK"
              bank_number_branch: "063063"
              currency_code: "AUD"
            - bank_acc_format_code: "XX"
              bank_number_formatted: "44463377"
              own_bank_number: "98765432"
              bank_business_relation_code: "BNK"
              bank_number_branch: "666455"
      register: supplier_banking_edited_again

    - name: Delete supplier 
      aux_suppliers:
        state: absent
        qad_server: "{{ aux.hostname }}"
        state_file: "{{ auth_state_file }}"
        input_fields:
          main:
            supplier_code: 5ST000
      register: supplier_deleted

    - name: Try to delete supplier again
      aux_suppliers:
        state: absent
        qad_server: "{{ aux.hostname }}"
        state_file: "{{ auth_state_file }}"
        input_fields:
          main:
            supplier_code: 5ST000
      register: supplier_deleted_again

    - name: Logout
      aux_auth:
        state: absent
        qad_server: "{{ aux.hostname }}"
        state_file: "{{ auth_state_file }}"

    - name: Assert all tasks
      assert:
        that:
          - supplier_created.changed == True
          - supplier_not_modified.changed == False
          - supplier_edited.changed == True
          - supplier_edited_again.changed == False
          - supplier_banking_edited.changed == True
          - supplier_banking_edited_again.changed == False
          - supplier_deleted.changed == True
          - supplier_deleted_again.changed == False

