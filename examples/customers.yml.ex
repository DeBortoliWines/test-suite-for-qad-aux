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
            customer_code: 2JOE001
            address:
              business_relation_name: Joes customer
              address_search_name: Joes customer
              city: Sydney
            accounting_profile:
              invoice_control_gl_profile_code: 10101-CRPAUS-A
              credit_note_control_gl_profile_code: 10101-CRPAUS-A
              pre_payment_control_gl_profile_code: 10101-CRPAUS-A
              sales_account_gl_profile_code: 20202-CRPAUS-SA
            payment:
              credit_terms_code: AP07
              invoice_status_code: AP-INITIAL
            tax:
              tax_zone: 10
      register: customer_created

    - name: Edit customer name
      aux_customers:
        state: present
        qad_server: "{{ aux.hostname }}"
        state_file: "{{ auth_state_file }}"
        input_fields:
          main:
            customer_code: 2JOE001
            address:
              business_relation_name: Joes COOL customer
              address_search_name: Joes customer
              city: Sydney
            accounting_profile:
              invoice_control_gl_profile_code: 10101-CRPAUS-A
              credit_note_control_gl_profile_code: 10101-CRPAUS-A
              pre_payment_control_gl_profile_code: 10101-CRPAUS-A
              sales_account_gl_profile_code: 20202-CRPAUS-SA
            payment:
              credit_terms_code: AP07
              invoice_status_code: AP-INITIAL
            tax:
              tax_zone: 10
      register: customer_edited

    - name: Try to edit customer name again to same value
      aux_customers:
        state: present
        qad_server: "{{ aux.hostname }}"
        state_file: "{{ auth_state_file }}"
        input_fields:
          main:
            customer_code: 2JOE001
            address:
              business_relation_name: Joes COOL customer
              address_search_name: Joes customer
              city: Sydney
            accounting_profile:
              invoice_control_gl_profile_code: 10101-CRPAUS-A
              credit_note_control_gl_profile_code: 10101-CRPAUS-A
              pre_payment_control_gl_profile_code: 10101-CRPAUS-A
              sales_account_gl_profile_code: 20202-CRPAUS-SA
            payment:
              credit_terms_code: AP07
              invoice_status_code: AP-INITIAL
            tax:
              tax_zone: 10
      register: customer_edited_again

    - name: Delete customer 
      aux_customers:
        state: absent
        qad_server: "{{ aux.hostname }}"
        state_file: "{{ auth_state_file }}"
        input_fields:
          main:
            customer_code: 2JOE001
      register: customer_deleted

    - name: Try to delete customer again
      aux_customers:
        state: absent
        qad_server: "{{ aux.hostname }}"
        state_file: "{{ auth_state_file }}"
        input_fields:
          main:
            customer_code: 2JOE001
      register: customer_deleted_again

    - name: Logout
      aux_auth:
        state: absent
        qad_server: "{{ aux.hostname }}"
        state_file: "{{ auth_state_file }}"

    - name: Assert all tasks
      assert:
        that:
          - customer_created.changed == True
          - customer_edited.changed == True
          - customer_edited_again.changed == False
          - customer_deleted.changed == True
          - customer_deleted_again.changed == False

