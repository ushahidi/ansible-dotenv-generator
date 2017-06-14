#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'supported_by': 'Ushahidi Team'}

DOCUMENTATION = '''
---
module: parse_dotenv_sample
author: "Ushahidi Team (team@ushahidi.com)"
short_description: Parse sample dotenv file into jinja2 template
description:
  - This module parses a sample dotenv file into a jinja2 template
  - The entries in the sample file are parsed the following way
    - `VAR_NAME=` translates to a required variable name without default.
      When evaluating the template, a value MUST be provided for this variable.
    - `VAR_NAME=default_value` translates to a variable name for which a
      default variable is provided. When evaluating the template, if a value
      is not provided for the variable, the default will be used
    - `VAR_NAME=""` translates to an optional variable name. When evaluating
      the template, if a value is not provided, the variable will default to
      empty.
  - Note that quoting may be used in the default values
  - Comments use the '#' symbol and will be discarded when producing the template
    - You may use the '#' symbol in default values, as long as it's not preceded
      by any white space. i.e:
      - `VAR_NAME=abc#def` gives the default value "abc#def".
      - `VAR_NAME=abc #def` gives the default value "abc" (#def is considered a comment)
      - `VAR_NAME="abc #def"` gives the default value "abc #def"
  - The template will be generated in the following fashion:
    - `VAR_NAME="{{ env.VAR_NAME }}"` for required variables
    - `VAR_NAME="{{ env.VAR_NAME | default("default_value") }}" for variables with a default value
    - the name of the dictionary variable that is expected to carry the values can be adjusted
      via the `env_dict_varname` option
  - Returns a dotenv_template_path variable in the result, containing a target side path to the
    generated template file 
options:
  dotenv_sample_path:
    required: true
    description:
      - Path to the dotenv sample file
  env_dict_varname:
    required: false
    default: "env"
    description:
      - Name of the dictionary variable that will be expected to carry the variable values when
        evaluating the template.
'''

import re
import os, os.path
from tempfile import NamedTemporaryFile
import pipes

def main():
  module = AnsibleModule(
    argument_spec = dict(
      dotenv_sample_path = dict(required=True),     # path to the dotenv sample file
      env_dict_varname = dict(default='env')        # name of the dict variable to use in the resulting template 
    )
  )
  try:
    dotenv_template_path = None
    template = _parse_dotenv_sample(module.params['dotenv_sample_path'], module.params['env_dict_varname'])
    with NamedTemporaryFile(delete=False) as f:
      f.write(template)
      dotenv_template_path = f.name
    module.exit_json(changed=True, dotenv_template_path=dotenv_template_path)
  except IOError as err:
    module.fail_json(msg="Error accessing file: %s" % str(err))
  except TypeError as err:
    module.fail_json(msg="Unexpected variable type: %s" % str(err))
  except AssertionError as err:
    module.fail_json(msg="Unexpectec condition: %s" % str(err))

# grep_line_re doc (matches relevant content in lines, discards comments)
#   ^\s*(\w+)=        ; words at the beginning of the line (optionally preceded by whitespace) followed by sign '='
#   ("([^"]|(?<=\\)")*")?     ; optional group of characters enclosed by quotes , where each character is either NOT '"' or '\"'
#   ('([^']|(?<=\\)')*')?     ; same as above but for single quotes
#   ([^#]|(?<!\s)#)*  ; optional group of characters stopping at '#' , but including '#' if it's not preceded by whitespace
_grep_line_re = re.compile(r"""^\s*(\w+)\s*=\s*("([^"]|(?<=\\)")*")?('([^']|(?<=\\)')*')?([^#]|(?<!\s)#)*""")

# _name_and_value_re (separates variable name and default value in groups) , matches three groups in the line
#   1. (\w+)   ; name of the variable (i.e. VAR_NAME)
#   2. (["'].*)?  ; optionally, any content starting with quote
#   3. (.*)?   ; optionally, any content
_name_and_value_re = re.compile(r"""^(\w+)\s*=\s*(["'].*)?(.*)?$""")

def _parse_dotenv_sample(dotenv_sample_path, env_dict_varname):
  t = ""    # The resulting template
  with open(dotenv_sample_path, 'r') as f:
    for line in f:
      # find relevant content in line
      env_spec = _grep_line_re.match(line)
      if env_spec:
        env_spec = env_spec.group().strip()
        # match variable name and optional default value
        (var_name, q_default, default) = _name_and_value_re.match(env_spec).groups()
        assert(not (q_default and default))  # two default values is fishy business
        if default:   # we always quote the default value, because otherwise default() doesn't work
          q_default = pipes.quote(default)
          if q_default[0] not in ("'", '"'):
            q_default = "'" + q_default + "'"
        if not q_default:
          t = t + '{v}={{{{ {e}.{v} | string | quote }}}}\n'.format(v=var_name, e=env_dict_varname)
        else:
          t = t + '{v}={{{{ {e}.{v} | default({d}) | string | quote }}}}\n'.format(v=var_name, e=env_dict_varname, d=q_default)

  return t;

if __name__ == '__main__':
  main()

