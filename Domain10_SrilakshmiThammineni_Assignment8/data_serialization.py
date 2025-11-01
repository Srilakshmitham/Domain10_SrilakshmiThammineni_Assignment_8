import re

def _token_to_primitive(token):
    t = token.strip()
    if t == '': return ''
    if t.lower() == 'null': return None
    if t.lower() == 'true': return True
    if t.lower() == 'false': return False
    if re.fullmatch(r'-?\d+', t): return int(t)
    if re.fullmatch(r'-?\d+\.\d+', t): return float(t)
    return t

class _ColonParser:
    def __init__(self, s):
        self.s = s; self.i = 0; self.n = len(s)
    def _peek(self): return self.s[self.i] if self.i < self.n else None
    def _next(self): ch = self._peek(); self.i += 1; return ch
    def _consume_whitespace(self):
        while self._peek() and self._peek().isspace(): self._next()
    def parse_value(self):
        self._consume_whitespace(); ch = self._peek()
        if ch == '{': return self.parse_object()
        if ch == '[': return self.parse_list()
        token = []
        while True:
            ch = self._peek()
            if ch is None or ch in [';', '}', ']']: break
            token.append(self._next())
        return _token_to_primitive(''.join(token).strip())
    def parse_list(self):
        self._next(); items = []
        while True:
            self._consume_whitespace()
            if self._peek() == ']': self._next(); break
            if self._peek() == '{': items.append(self.parse_object())
            elif self._peek() == '[': items.append(self.parse_list())
            else:
                token = []
                while True:
                    ch = self._peek()
                    if ch is None or ch in [',', ']']: break
                    token.append(self._next())
                items.append(_token_to_primitive(''.join(token).strip()))
            self._consume_whitespace()
            if self._peek() == ',': self._next(); continue
            if self._peek() == ']': continue
        return items
    def parse_object(self):
        self._next(); obj = {}
        while True:
            self._consume_whitespace()
            if self._peek() == '}': self._next(); break
            key_chars = []
            while True:
                ch = self._peek()
                if ch is None or ch == ':': break
                key_chars.append(self._next())
            key = ''.join(key_chars).strip()
            if self._peek() == ':': self._next()
            val = self.parse_value(); obj[key] = val
            self._consume_whitespace()
            if self._peek() == ';': self._next(); continue
            if self._peek() == '}': continue
            if self._peek() is None: break
        return obj

def parse_colon_format(s):
    parser = _ColonParser(s)
    parser._consume_whitespace(); ch = parser._peek()
    if ch == '{': return parser.parse_object()
    obj = {}
    while parser._peek():
        parser._consume_whitespace(); key_chars = []
        while parser._peek() and parser._peek() != ':': key_chars.append(parser._next())
        key = ''.join(key_chars).strip()
        if parser._peek() == ':': parser._next()
        val = parser.parse_value(); obj[key] = val
        parser._consume_whitespace()
        if parser._peek() == ';': parser._next(); continue
        else: break
    return obj

def serialize_colon(obj):
    if obj is None: return 'null'
    if isinstance(obj, bool): return 'true' if obj else 'false'
    if isinstance(obj, (int, float)): return str(obj)
    if isinstance(obj, str):
        if any(c in obj for c in ';:{}[],'):
            esc = ''.join('\\' + c if c in ';:{}[],\\' else c for c in obj)
            return esc
        return obj
    if isinstance(obj, list):
        return '[' + ','.join(serialize_colon(x) for x in obj) + ']'
    if isinstance(obj, dict):
        parts = []
        for k, v in obj.items():
            parts.append(f"{k}:{serialize_colon(v)}")
        return '{' + ';'.join(parts) + '}'
    return str(obj)

def serialize_pipe(obj, indent=0):
    lines = []; ind = '    ' * indent
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, dict):
                lines.append(f"{ind}{k}|")
                lines.extend(serialize_pipe(v, indent + 1))
            elif isinstance(v, list):
                lines.append(f"{ind}{k}|")
                for item in v:
                    if isinstance(item, (dict, list)):
                        lines.append(f"{ind}    -")
                        if isinstance(item, dict):
                            lines.extend(serialize_pipe(item, indent + 2))
                        else:
                            for it in item: lines.append(f"{ind}        - {it}")
                    else: lines.append(f"{ind}    - {item}")
            else: lines.append(f"{ind}{k}|{v}")
    else:
        if isinstance(obj, list):
            for item in obj: lines.append(f"{ind}- {item}")
        else: lines.append(f"{ind}{obj}")
    return lines

def parse_pipe_format(s):
    lines = [ln.rstrip() for ln in s.splitlines() if ln.strip() != '']
    parsed = []
    for ln in lines:
        m = re.match(r'^( *)(.*)$', ln)
        spaces, content = m.group(1), m.group(2)
        indent = len(spaces) // 4
        parsed.append((indent, content))
    i = 0
    def build_block(current_indent):
        nonlocal i
        result = {}
        while i < len(parsed):
            indent, content = parsed[i]
            if indent < current_indent: break
            if indent > current_indent: i += 1; continue
            i += 1
            if content.startswith('- '):
                key = None; value = _token_to_primitive(content[2:].strip())
                if not isinstance(result, list): result = [value]
                else: result.append(value)
                continue
            if '|' in content:
                key, valpart = content.split('|', 1)
                key = key.strip(); valpart = valpart.strip()
                if valpart == '':
                    child = build_block(current_indent + 1); result[key] = child
                else:
                    if valpart.startswith('- '): result[key] = _token_to_primitive(valpart[2:].strip())
                    else: result[key] = _token_to_primitive(valpart)
            else: result[content.strip()] = ''
        return result
    i = 0
    return build_block(0)

def convert_format(data_str, from_format, to_format):
    if from_format == 'COLON': obj = parse_colon_format(data_str)
    elif from_format == 'PIPE': obj = parse_pipe_format(data_str)
    else: raise ValueError("Unsupported from_format")
    if to_format == 'COLON': return serialize_colon(obj)
    elif to_format == 'PIPE': return '\n'.join(serialize_pipe(obj))
    elif to_format == 'OBJ': return obj
    else: raise ValueError("Unsupported to_format")

def validate_schema(obj, schema):
    errors = []
    def _validate(value, sch, path=''):
        if isinstance(sch, dict):
            if not isinstance(value, dict):
                errors.append(f"{path or '/'}: expected object"); return
            for key, subsch in sch.items():
                if key not in value: errors.append(f"{path}/{key}: missing")
                else: _validate(value[key], subsch, f"{path}/{key}")
        elif isinstance(sch, list):
            if not isinstance(value, list): errors.append(f"{path}: expected list")
            else:
                subsch = sch[0] if sch else None
                for idx, item in enumerate(value):
                    if subsch: _validate(item, subsch, f"{path}[{idx}]")
        elif sch in (int, float, str, bool):
            typ = {int:int, float:float, str:str, bool:bool}[sch]
            if not isinstance(value, typ): errors.append(f"{path}: expected {sch.__name__}")
        elif sch is None:
            if value is not None: errors.append(f"{path}: expected null")
        else:
            try:
                if not sch(value): errors.append(f"{path}: custom validator failed")
            except Exception: errors.append(f"{path}: custom validator exception")
    _validate(obj, schema, '')
    return errors

if __name__ == "__main__":
    colon_sample = "name:John Doe;age:30;tags:[dev,python];address:{city:Delhi;zip:110001};active:true"
    obj = parse_colon_format(colon_sample)
    pipe_text = convert_format(colon_sample, 'COLON', 'PIPE')
    back_colon = convert_format(pipe_text, 'PIPE', 'COLON')
    schema = {
        "name": str,
        "age": int,
        "tags": [str],
        "address": {"city": str, "zip": int},
        "active": bool
    }
    errs = validate_schema(obj, schema)
    print(obj)
    print(pipe_text)
    print(back_colon)
    print(errs if errs else "Schema OK")
