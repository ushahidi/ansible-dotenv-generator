ansible-dotenv-generator
========================

Generate dotenv files to go in your hosts.

Role Variables
--------------

* `dotenv_sample`: path in the host containing a sample dotenv file
* `env`: dictionary with key/value pairs to fill into the env file
* `dest`: path in the host where the generated dotenv file should be placed
* `dest_mode`: (default: `0644`) mode to apply to the generated file
* `dest_owner`: (optional) user to own the generated file
* `dest_group`: (optional) group to own the generated file

Description of operation
------------------------

The sample dotenv file (indicated by `dotenv_sample`) is transformed into a Jinja2 template. 

Essentially, if the sample dotenv file is:

```
VAR_1=         # required variable
VAR_2=default  # variable with default
VAR_3=""       # variable with empty default
```

the generated Jinja2 template will be:

```
VAR_1={{ env.VAR_1 | string | quote }}
VAR_2={{ env.VAR_2 | default("default") | string | quote }}
VAR_3={{ env.VAR_3 | default("") | string | quote }}
```

See comments [./library/parse_dotenv_sample.py](./library/parse_dotenv_sample.py) for details.

Once the template is generated, the variables in the `env` dictionary are applied to it and the final dotenv file is generated.

Example Playbook
----------------

    - hosts: servers
      roles:
         - role: ansible-dotenv-generator
           dotenv_sample: /home/myproject/.env.sample
           env:
             VAR_1: hello
             VAR_2: world
           dest: /home/myproject/.env

License
-------

BSD

Author Information
------------------

Ushahidi Team
