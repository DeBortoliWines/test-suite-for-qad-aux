---
- hosts: all

  pre_tasks:
    - include_vars: ../vars/credentials.yml

  tasks:
    - name: Set Playbook Facts
      set_fact:
        auth_state_file: state.json

    - name: Login to QAD
      no_log: True
      aux_auth:
        state: present
        qad_server: "{{ aux.hostname }}"
        state_file: "{{ auth_state_file }}"
        headless: True
        username: "{{ aux.username }}"
        password: "{{ aux.password }}"
      register: login

    - name: Try to login again
      no_log: True
      aux_auth:
        state: present
        qad_server: "{{ aux.hostname }}"
        state_file: "{{ auth_state_file }}"
        username: "{{ aux.username }}"
        password: "{{ aux.password }}"
      register: login_again

    - name: Logout
      no_log: True
      aux_auth:
        state: absent
        qad_server: "{{ aux.hostname }}"
        state_file: "{{ auth_state_file }}"
      register: logout

    - name: Try go logout again
      no_log: True
      aux_auth:
        state: absent
        qad_server: "{{ aux.hostname }}"
        state_file: "{{ auth_state_file }}"
      register: logout_again

    - name: Assert all tasks
      assert:
        that:
          - login.changed == True
          - login_again.changed == False
          - logout.changed == True
          - logout_again.changed == False
