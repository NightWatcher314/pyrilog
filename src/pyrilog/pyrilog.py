import enum
import string


class VAR_TYPE(enum.Enum):
    WIRE = "wire"
    REG = "reg"
    DEFAULT = ""


class BaseBlock:
    _current_instance_stack = []

    def __init__(self) -> None:
        self.body = []

    def __enter__(self):
        BaseBlock._current_instance_stack.append(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if len(BaseBlock._current_instance_stack) > 1:
            father_block = BaseBlock._current_instance_stack[-2]
            father_block.add_block(self)
        BaseBlock._current_instance_stack.pop()
        if exc_type:
            print(f"An exception of type {exc_type} occurred.")
            print(f"Exception value: {exc_val}")
            print(f"Traceback: {exc_tb}")

    def add_body(self, line: str):
        self.body.append(line)

    def generate(self) -> str:
        return "\n".join(self.body)

    def add_block(self, block):
        self.add_body(block.generate())


class ModuleBlock(BaseBlock):
    def __init__(self, module_name: str):
        super().__init__()
        self.module_name = module_name
        self.parameters = []
        self.inputs = []
        self.outputs = []
        self.inouts = []

    def generate(self) -> str:
        parts = [f"module {self.module_name}"]

        if self.parameters:
            parts.extend([" #(", ",\n".join(self.parameters), ")"])

        all_ports = self.inputs + self.outputs + self.inouts
        if all_ports:
            parts.extend([" (", ",\n".join(all_ports), ");"])
        else:
            parts.append(";")

        if self.body:
            parts.extend(["\n", "\n".join(self.body)])

        parts.append("\nendmodule")
        return "".join(parts)


class AlwaysFFBlock(BaseBlock):
    def __init__(self, clk: str = "clk", rst: str = None):
        super().__init__()
        self.clk = clk
        self.rst = rst

    def generate(self) -> str:
        if self.rst:
            sensitivity = f"posedge {self.clk}, negedge {self.rst}"
        else:
            sensitivity = f"posedge {self.clk}"
        return f"always_ff @({sensitivity}) begin\n" + "\n".join(self.body) + "\nend"


class AlwaysCombBlock(BaseBlock):
    def generate(self) -> str:
        return "always_comb begin\n" + "\n".join(self.body) + "\nend"


class IfBlock(BaseBlock):
    def __init__(self, condition: str = "rstn"):
        super().__init__()
        self.condition = condition

    def generate(self) -> str:
        return f"if ({self.condition}) begin\n" + "\n".join(self.body) + "\nend"


class ElseBlock(BaseBlock):
    def generate(self) -> str:
        return "else begin\n" + "\n".join(self.body) + "\nend"


class CaseBlock(BaseBlock):
    def __init__(self, case_expr: str):
        super().__init__()
        self.case_expr = case_expr

    def generate(self) -> str:
        return f"case ({self.case_expr})\n" + "\n".join(self.body) + "\nendcase"


class CaseItemBlock(BaseBlock):
    def __init__(self, value: str):
        super().__init__()
        self.value = value

    def generate(self) -> str:
        return f"{self.value}: begin\n" + "\n".join(self.body) + "\nend"


class VerilogGenerator(BaseBlock):
    pass


def _format_dimensions(width, dimensions) -> tuple[str, str]:
    if isinstance(width, int):
        width_str = "" if width == 1 else f"[{width - 1}:0] "
    else:
        width_str = "" if width == "1" else f"[{width}-1:0] "

    if dimensions is None:
        return width_str, ""

    if isinstance(dimensions, (int, str)):
        dimensions = [dimensions]

    dim_str = ""
    for dim in dimensions:
        if isinstance(dim, int):
            dim_str += f"[{dim - 1}:0]"
        else:
            dim_str += f"[{dim}-1:0]"

    return width_str, dim_str


def _port_sentence(
    port_type: str, var_type: str, name: str, width=1, dimensions=None
) -> str:
    # Validate var_type
    valid_types = {"", "wire", "reg"}
    if var_type not in valid_types:
        raise ValueError(
            f"Invalid var_type '{var_type}'. Must be one of: {valid_types}"
        )

    var_str = f"{var_type} " if var_type else ""
    width_str, dim_str = _format_dimensions(width, dimensions)
    return f"{port_type} {var_str}{width_str}{name}{dim_str}"


def _find_father() -> BaseBlock:
    return BaseBlock._current_instance_stack[-1]


def add_body(line: str):
    _find_father().add_body(line)


def add_newline():
    add_body("")


def add_parameter(name: str, value: str):
    module = _find_father()
    assert isinstance(module, ModuleBlock), "Parameters can only be added to modules"
    module.parameters.append(f"parameter {name} = {value}")


def add_input(name: str, width=1, dimensions=None, var_type: str = ""):
    module = _find_father()
    assert isinstance(module, ModuleBlock), "Inputs can only be added to modules"
    module.inputs.append(_port_sentence("input", var_type, name, width, dimensions))


def add_output(name: str, width=1, dimensions=None, var_type: str = ""):
    module = _find_father()
    assert isinstance(module, ModuleBlock), "Outputs can only be added to modules"
    module.outputs.append(_port_sentence("output", var_type, name, width, dimensions))


def add_inout(name: str, width=1, dimensions=None, var_type: str = ""):
    module = _find_father()
    assert isinstance(module, ModuleBlock), "Inouts can only be added to modules"
    module.inouts.append(_port_sentence("inout", var_type, name, width, dimensions))


def add_assign(out_var: str, out_indices: list, in_var: str, in_indices: list):
    out_idx = "".join(f"[{idx}]" for idx in out_indices)
    in_idx = "".join(f"[{idx}]" for idx in in_indices)
    _find_father().add_body(f"assign {out_var}{out_idx} = {in_var}{in_idx};")


def add_instance(module_name: str, instance_name: str, parameters: dict, ports: dict):
    lines = [module_name]

    if parameters:
        param_list = [f"    .{name}({value})" for name, value in parameters.items()]
        lines = [f"{module_name} #(", ",\n".join(param_list), ")"]

    port_list = [f"    .{name}({signal})" for name, signal in ports.items()]
    lines.extend([f"{instance_name} (", ",\n".join(port_list), ");"])

    _find_father().add_body("\n".join(lines))


def add_var(var_type: VAR_TYPE, name: str, width=1, dimensions=None):
    width_str, dim_str = _format_dimensions(width, dimensions)
    _find_father().add_body(f"{var_type.value} {width_str}{name}{dim_str};")


def add_wire(name: str, width=1, dimensions=None):
    add_var(VAR_TYPE.WIRE, name, width, dimensions)


def add_reg(name: str, width=1, dimensions=None):
    add_var(VAR_TYPE.REG, name, width, dimensions)


def add_case_item(value: str, statement: str = None):
    if statement:
        _find_father().add_body(f"{value}: {statement}")
        return None
    else:
        return CaseItemBlock(value)


def add_case_default(statement: str = None):
    if statement:
        _find_father().add_body(f"default: {statement}")
    else:
        _find_father().add_body("default: begin")
