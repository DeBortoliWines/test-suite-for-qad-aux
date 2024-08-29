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
          
    - name: Create new Business Relation
      aux_business_relations:
        state: present
        qad_server: "{{ aux.hostname }}"
        headless: True
        state_file: "{{ auth_state_file }}"
        input_fields:
          main:
            business_relation_code: 70-707
            business_relation_name1: John Doe
            business_relation_search_name: John Doe
            addresses:
              head_office:
                head_office_street1: 1 Woollomooloo Rd
                head_office_zip_code: 2000
                head_office_city: Sydney
                head_office_state_code: NSW
                head_office_telephone: 02 9999 0000
                head_office_email: ansible@qad.com
                head_office_web_site: https://www.qad.com
      register: business_relation_created

    - name: Edit Business Relation
      aux_business_relations:
        state: present
        qad_server: "{{ aux.hostname }}"
        headless: True
        state_file: "{{ auth_state_file }}"
        input_fields:
          main:
            business_relation_code: 70-707
            business_relation_name1: John Stag
            business_relation_search_name: John Doe
            addresses:
              head_office:
                head_office_street1: 1 Woollomooloo Rd
                head_office_zip_code: 2000
                head_office_city: Sydney
                head_office_state_code: NSW
                head_office_telephone: 02 9999 0000
                head_office_email: ansible@qad.com
                head_office_web_site: https://www.qad.com
      register: business_relation_edited

    - name: Edit Business Relation to same name again
      aux_business_relations:
        state: present
        qad_server: "{{ aux.hostname }}"
        headless: True
        state_file: "{{ auth_state_file }}"
        input_fields:
          main:
            business_relation_code: 70-707
            business_relation_name1: John Stag
            business_relation_search_name: John Doe
            addresses:
              head_office:
                head_office_street1: 1 Woollomooloo Rd
                head_office_zip_code: 2000
                head_office_city: Sydney
                head_office_state_code: NSW
                head_office_telephone: 02 9999 0000
                head_office_email: ansible@qad.com
                head_office_web_site: https://www.qad.com
      register: business_relation_edited_again

    - name: Delete Business Relation
      aux_business_relations:
        state: absent
        qad_server: "{{ aux.hostname }}"
        headless: True
        state_file: "{{ auth_state_file }}"
        input_fields:
          main:
            business_relation_code: 70-707
      register: business_relation_deleted

    - name: Delete Business Relation again
      aux_business_relations:
        state: absent
        qad_server: "{{ aux.hostname }}"
        headless: True
        state_file: "{{ auth_state_file }}"
        input_fields:
          main:
            business_relation_code: 70-707
      register: business_relation_deleted_again

    - name: Logout
      aux_auth:
        state: absent
        qad_server: "{{ aux.hostname }}"
        state_file: "{{ auth_state_file }}"

    - name: Assert all tasks
      assert:
        that:
          - business_relation_created.changed == True
          - business_relation_edited.changed == True
          - business_relation_edited_again.changed == False
          - business_relation_deleted.changed == True
          - business_relation_deleted_again.changed == False
