# Pyrilog

一个基于 Python 上下文管理器的 SystemVerilog 代码生成工具。使用简洁的 Python 语法生成结构化的硬件描述语言代码。

## 特性

- 🏗️ **层次化设计**: 基于上下文管理器的嵌套块结构
- 🎯 **简洁 API**: 使用 `v_` 前缀的短别名，代码更加简洁
- 🔄 **case 语句支持**: 支持单语句和多语句两种 case 语句写法
- 🧩 **模块化**: 支持参数化模块、实例化、多维数组等
- 🚀 **现代语法**: 生成 SystemVerilog `always_ff`、`always_comb` 语法

## 安装

```bash
pip install pyrilog
```

## 快速开始

### 基本模块定义

```python
from pyrilog import *

with v_gen() as gen:
    with v_module("counter"):
        # 参数定义
        v_param("WIDTH", "8")
        
        # 端口定义
        v_input("clk")
        v_input("rst_n") 
        v_input("data_in", "WIDTH")
        v_output("count", "WIDTH", None, "reg")

print(gen.generate())
```

生成的 SystemVerilog 代码：

```systemverilog
module counter #(
parameter WIDTH = 8
) (
input clk,
input rst_n,
input [WIDTH-1:0] data_in,
output reg [WIDTH-1:0] count
);
endmodule
```

### 时序逻辑 - 计数器

```python
from pyrilog import *

with v_gen() as gen:
    with v_module("counter"):
        v_param("WIDTH", "8")
        v_input("clk")
        v_input("rst_n")
        v_output("count", "WIDTH", None, "reg")
        
        # SystemVerilog always_ff 块  
        with v_always_ff("clk", "rst_n"):
            with v_if("!rst_n"):
                v_body("count <= '0;")
            with v_else():
                v_body("count <= count + 1'b1;")

with open("counter.sv", "w") as f:
    f.write(gen.generate())
```

### Case 语句 - ALU 设计

Pyrilog 支持两种 case 语句写法：

#### 1. 单语句模式

```python
from pyrilog import *

with v_gen() as gen:
    with v_module("simple_alu"):
        v_input("opcode", 3)
        v_input("a", 8)
        v_input("b", 8) 
        v_output("result", 8, None, "reg")
        
        with v_always_comb():
            with v_case("opcode"):
                v_case_item("3'b000", "result = a + b;")
                v_case_item("3'b001", "result = a - b;")
                v_case_item("3'b010", "result = a & b;")
                v_case_default("result = 8'h00;")

print(gen.generate())
```

#### 2. 多语句模式（使用上下文管理器）

```python
from pyrilog import *

with v_gen() as gen:
    with v_module("complex_alu"):
        v_input("clk")
        v_input("rst_n")
        v_input("opcode", 4)
        v_input("a", 16)
        v_input("b", 16)
        v_output("result", 16, None, "reg")
        v_output("valid", 1, None, "reg")
        v_output("overflow", 1, None, "reg")
        
        with v_always_ff("clk", "rst_n"):
            with v_if("!rst_n"):
                v_body("result <= 16'h0000;")
                v_body("valid <= 1'b0;")
                v_body("overflow <= 1'b0;")
            with v_else():
                with v_case("opcode"):
                    # 单语句 case
                    v_case_item("4'b0000", "result <= a + b;")
                    v_case_item("4'b0001", "result <= a - b;")
                    
                    # 多语句 case，使用 with 上下文管理器
                    with v_case_item("4'b0010"):  # 位与运算，带有效信号
                        v_body("result <= a & b;")
                        v_body("valid <= 1'b1;")
                        v_body("overflow <= 1'b0;")
                    
                    with v_case_item("4'b0011"):  # 位或运算，带溢出检测
                        v_body("result <= a | b;")
                        v_body("valid <= 1'b1;")
                        v_body("overflow <= (a[15] | b[15]) & !result[15];")
                    
                    # 默认情况
                    v_case_default("result <= 16'h0000;")
                
                v_body("valid <= 1'b1;")  # case 外的公共语句

print(gen.generate())
```

生成的 SystemVerilog 代码：

```systemverilog
module complex_alu (
input clk,
input rst_n,
input [3:0] opcode,
input [15:0] a,
input [15:0] b,
output reg [15:0] result,
output reg valid,
output reg overflow
);
always_ff @(posedge clk, negedge rst_n) begin
if (!rst_n) begin
result <= 16'h0000;
valid <= 1'b0;
overflow <= 1'b0;
end
else begin
case (opcode)
4'b0000: result <= a + b;
4'b0001: result <= a - b;
4'b0010: begin
result <= a & b;
valid <= 1'b1;
overflow <= 1'b0;
end
4'b0011: begin
result <= a | b;
valid <= 1'b1;
overflow <= (a[15] | b[15]) & !result[15];
end
default: result <= 16'h0000;
endcase
valid <= 1'b1;
end
end
endmodule
```

### 多维数组支持

```python
from pyrilog import *

with v_gen() as gen:
    with v_module("memory_array"):
        v_input("clk")
        v_input("addr", 8)
        v_input("wr_data", 32)
        v_output("rd_data", 32, None, "reg")
        
        # 创建二维内存数组：32位宽，256x4 的数组
        v_reg("memory", 32, [256, 4])
        
        # 一维数组：32位宽，16个元素
        v_wire("buffer", 32, 16)

print(gen.generate())
```

### 模块实例化

```python
from pyrilog import *

with v_gen() as gen:
    with v_module("cpu_top"):
        v_input("clk")
        v_input("rst_n")
        v_input("instruction", 32)
        v_output("result", 32, None, "wire")
        
        # 实例化 ALU 模块
        v_inst("complex_alu", "alu_inst", 
               {"WIDTH": "32"},  # 参数
               {                 # 端口连接
                   "clk": "clk",
                   "rst_n": "rst_n", 
                   "opcode": "instruction[3:0]",
                   "a": "instruction[31:16]",
                   "b": "instruction[15:4]",
                   "result": "result"
               })

print(gen.generate())
```

## API 参考

### 核心块结构
- `v_gen()`: 顶层生成器
- `v_module(name)`: 模块定义
- `v_always_ff(clk, rst=None)`: always_ff 时序逻辑块  
- `v_always_comb()`: always_comb 组合逻辑块
- `v_if(condition)`: 条件语句
- `v_else()`: else 语句
- `v_case(expression)`: case 语句

### Case 语句
- `v_case_item(value, statement=None)`: case 项
  - 单语句：`v_case_item("3'b001", "result = a + b;")`
  - 多语句：`with v_case_item("3'b001"): ...`
- `v_case_default(statement=None)`: 默认 case

### 端口和变量
- `v_input(name, width=1, dimensions=None, var_type="")`: 输入端口
- `v_output(name, width=1, dimensions=None, var_type="")`: 输出端口  
- `v_inout(name, width=1, dimensions=None, var_type="")`: 双向端口
- `v_wire(name, width=1, dimensions=None)`: wire 信号
- `v_reg(name, width=1, dimensions=None)`: reg 信号

### 其他功能
- `v_param(name, value)`: 参数定义
- `v_assign(out_var, out_indices, in_var, in_indices)`: assign 语句
- `v_inst(module_name, inst_name, params, ports)`: 模块实例化
- `v_body(code)`: 添加原始代码行

## 维度格式

支持多种维度表示方法：

```python
# 位宽
v_reg("data", 8)        # [7:0] data
v_reg("data", "WIDTH")  # [WIDTH-1:0] data

# 一维数组
v_reg("mem", 8, 16)     # [7:0] mem[15:0] 
v_reg("mem", 8, [16])   # [7:0] mem[15:0]

# 多维数组  
v_reg("mem", 8, [16, 4]) # [7:0] mem[15:0][3:0]
```

## 许可证

本项目采用 MIT 许可证。详情请见 [LICENSE](LICENSE) 文件。