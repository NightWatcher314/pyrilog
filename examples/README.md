# Pyrilog 示例

本目录包含 Pyrilog 的使用示例，展示如何使用新的 case 语句功能和其他高级特性。

## 示例1: 简单的 ALU 设计

**位置**: `examples/example1/main.py`

演示内容:
- ✅ **Case 语句的两种用法**：单语句和多语句模式
- ✅ **参数化模块设计**：使用参数控制位宽
- ✅ **时序逻辑**：`always_ff` 块的使用
- ✅ **条件语句**：`if/else` 嵌套结构

生成的模块:
- `simple_alu.sv`: 8位 ALU，支持加减法、位运算、移位操作
- `counter.sv`: 参数化计数器，带溢出检测

运行示例:
```bash
cd examples/example1
python main.py
```

### 关键代码片段:

**单语句 case**:
```python
with v_case("opcode"):
    v_case_item("3'b000", "result <= a + b;")        # 加法
    v_case_item("3'b001", "result <= a - b;")        # 减法
```

**多语句 case (使用 with)**:
```python
with v_case("opcode"):
    with v_case_item("3'b101"):  # 左移带溢出检测
        v_body("result <= a << 1;")
        v_body("if (a[DATA_WIDTH-1]) valid <= 1'b0;")
        v_body("else valid <= 1'b1;")
```

---

## 示例2: 复杂的 FIFO 系统

**位置**: `examples/example2/main.py`

演示内容:
- 🚀 **参数化同步 FIFO**：深度和位宽可配置
- 🔄 **状态机设计**：FIFO 控制器状态机
- 📦 **模块实例化**：顶层模块集成子模块
- 🎯 **多维数组**：内存数组的使用
- ⚡ **复杂 case 语句**：状态转移逻辑

生成的模块:
- `sync_fifo.sv`: 参数化同步FIFO，支持16深度x32位
- `fifo_controller.sv`: 5状态的FIFO控制器
- `fifo_system.sv`: 集成FIFO和控制器的顶层模块

运行示例:
```bash
cd examples/example2  
python main.py
```

### 关键特性:

**参数化设计**:
```python
v_param("DATA_WIDTH", "32")
v_param("FIFO_DEPTH", "16")
v_param("PTR_WIDTH", "$clog2(FIFO_DEPTH)")
```

**多维数组**:
```python
v_reg("memory", "DATA_WIDTH", ["FIFO_DEPTH"])  # 内存数组
```

**状态机的 case 语句**:
```python
with v_case("current_state"):
    # 多语句状态处理
    with v_case_item("IDLE"):
        v_body("if (start) next_state = WRITE;")
        v_body("else next_state = IDLE;")
    
    # 单语句状态处理
    v_case_item("FULL_CHECK", "next_state = ERROR;")
```

**模块实例化**:
```python
v_inst("sync_fifo", "u_fifo",
       {"DATA_WIDTH": "DATA_WIDTH", "FIFO_DEPTH": "FIFO_DEPTH"},
       {
           "clk": "clk",
           "rst_n": "rst_n",
           "wr_en": "wr_enable",
           # ... 更多端口连接
       })
```

---

## 运行所有示例

从 examples 根目录运行:

```bash
# 运行示例1
python example1/main.py

# 运行示例2  
python example2/main.py
```

## 生成的文件

所有生成的 SystemVerilog 文件都会保存在对应的示例目录中:

**Example1 生成文件**:
- `simple_alu.sv`
- `counter.sv`

**Example2 生成文件**:
- `sync_fifo.sv` 
- `fifo_controller.sv`
- `fifo_system.sv`

## 特性对比

| 特性 | 示例1 | 示例2 |
|------|-------|-------|
| Case 语句 | ✅ 基础用法 | ✅ 复杂状态机 |
| 参数化 | ✅ 简单参数 | ✅ 复杂参数计算 |
| 多维数组 | ❌ | ✅ 内存数组 |
| 模块实例化 | ❌ | ✅ 多模块集成 |
| 状态机 | ❌ | ✅ 5状态FSM |

## 下一步

尝试修改这些示例:
1. 更改 ALU 的操作码位宽和支持的操作
2. 调整 FIFO 的深度和数据位宽参数
3. 在状态机中添加新的状态和转移条件
4. 创建自己的模块并集成到顶层设计中