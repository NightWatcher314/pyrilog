#!/usr/bin/env python3
"""
示例2: 复杂的 FIFO 设计
演示参数化模块、状态机、多维数组等高级特性
"""

from pyrilog import *


def generate_fifo():
    """生成参数化的同步 FIFO 模块"""
    with v_gen() as gen:
        with v_module("sync_fifo"):
            # 参数定义
            v_param("DATA_WIDTH", "32")
            v_param("FIFO_DEPTH", "16")
            v_param("PTR_WIDTH", "$clog2(FIFO_DEPTH)")
            
            # 端口定义
            v_input("clk")
            v_input("rst_n")
            v_input("wr_en")
            v_input("rd_en")
            v_input("wr_data", "DATA_WIDTH")
            v_output("rd_data", "DATA_WIDTH", None, "reg")
            v_output("full", 1, None, "reg")
            v_output("empty", 1, None, "reg")
            v_output("count", "PTR_WIDTH+1", None, "reg")
            
            # 内部信号
            v_reg("memory", "DATA_WIDTH", ["FIFO_DEPTH"])  # 内存数组
            v_reg("wr_ptr", "PTR_WIDTH")
            v_reg("rd_ptr", "PTR_WIDTH") 
            v_reg("fifo_count", "PTR_WIDTH+1")
            
            # 控制信号
            v_wire("wr_allow")
            v_wire("rd_allow")
            
            v_newline()
            v_body("// 写使能和读使能逻辑")
            v_assign("wr_allow", [], "wr_en & !full", [])
            v_assign("rd_allow", [], "rd_en & !empty", [])
            
            v_newline()
            v_body("// 内存写操作")
            with v_always_ff("clk", "rst_n"):
                with v_if("!rst_n"):
                    v_body("wr_ptr <= {PTR_WIDTH{1'b0}};")
                with v_else():
                    with v_if("wr_allow"):
                        v_body("memory[wr_ptr] <= wr_data;")
                        with v_if("wr_ptr == FIFO_DEPTH - 1"):
                            v_body("wr_ptr <= {PTR_WIDTH{1'b0}};")
                        with v_else():
                            v_body("wr_ptr <= wr_ptr + 1'b1;")
            
            v_newline()
            v_body("// 内存读操作")
            with v_always_ff("clk", "rst_n"):
                with v_if("!rst_n"):
                    v_body("rd_ptr <= {PTR_WIDTH{1'b0}};")
                    v_body("rd_data <= {DATA_WIDTH{1'b0}};")
                with v_else():
                    with v_if("rd_allow"):
                        v_body("rd_data <= memory[rd_ptr];")
                        with v_if("rd_ptr == FIFO_DEPTH - 1"):
                            v_body("rd_ptr <= {PTR_WIDTH{1'b0}};")
                        with v_else():
                            v_body("rd_ptr <= rd_ptr + 1'b1;")
            
            v_newline()
            v_body("// FIFO 计数器和状态标志")
            with v_always_ff("clk", "rst_n"):
                with v_if("!rst_n"):
                    v_body("fifo_count <= {(PTR_WIDTH+1){1'b0}};")
                with v_else():
                    with v_case("{wr_allow, rd_allow}"):
                        v_case_item("2'b10", "fifo_count <= fifo_count + 1'b1;")  # 只写
                        v_case_item("2'b01", "fifo_count <= fifo_count - 1'b1;")  # 只读
                        v_case_default("fifo_count <= fifo_count;")               # 同时读写或都不操作
            
            # 状态标志生成
            with v_always_ff("clk", "rst_n"):
                with v_if("!rst_n"):
                    v_body("full <= 1'b0;")
                    v_body("empty <= 1'b1;")
                    v_body("count <= {(PTR_WIDTH+1){1'b0}};")
                with v_else():
                    v_body("count <= fifo_count;")
                    v_body("full <= (fifo_count == FIFO_DEPTH);")
                    v_body("empty <= (fifo_count == {(PTR_WIDTH+1){1'b0}});")
    
    return gen.generate()


def generate_state_machine():
    """生成一个状态机控制器"""
    with v_gen() as gen:
        with v_module("fifo_controller"):
            # 状态定义
            v_param("IDLE", "3'b000")
            v_param("WRITE", "3'b001") 
            v_param("READ", "3'b010")
            v_param("FULL_CHECK", "3'b011")
            v_param("ERROR", "3'b100")
            
            # 端口
            v_input("clk")
            v_input("rst_n")
            v_input("start")
            v_input("fifo_full")
            v_input("fifo_empty") 
            v_output("wr_en", 1, None, "reg")
            v_output("rd_en", 1, None, "reg")
            v_output("error", 1, None, "reg")
            
            # 状态寄存器
            v_reg("current_state", 3)
            v_reg("next_state", 3)
            
            v_newline()
            v_body("// 状态寄存器")
            with v_always_ff("clk", "rst_n"):
                with v_if("!rst_n"):
                    v_body("current_state <= IDLE;")
                with v_else():
                    v_body("current_state <= next_state;")
            
            v_newline()
            v_body("// 状态转移逻辑")
            with v_always_comb():
                with v_case("current_state"):
                    # IDLE 状态 - 多语句case，使用上下文管理器
                    with v_case_item("IDLE"):
                        v_body("if (start) next_state = WRITE;")
                        v_body("else next_state = IDLE;")
                    
                    # WRITE 状态
                    with v_case_item("WRITE"):
                        v_body("if (fifo_full) next_state = FULL_CHECK;")
                        v_body("else next_state = READ;")
                    
                    # READ 状态
                    with v_case_item("READ"):
                        v_body("if (fifo_empty) next_state = IDLE;")
                        v_body("else next_state = READ;")
                    
                    # FULL_CHECK 状态
                    v_case_item("FULL_CHECK", "next_state = ERROR;")  # 单语句case
                    
                    # ERROR 状态
                    with v_case_item("ERROR"):
                        v_body("if (!start) next_state = IDLE;")
                        v_body("else next_state = ERROR;")
                    
                    # 默认状态
                    v_case_default("next_state = IDLE;")
            
            v_newline()
            v_body("// 输出逻辑")
            with v_always_comb():
                v_body("wr_en = (current_state == WRITE) && !fifo_full;")
                v_body("rd_en = (current_state == READ) && !fifo_empty;")
                v_body("error = (current_state == ERROR);")
    
    return gen.generate()


def generate_top_module():
    """生成顶层模块，集成 FIFO 和控制器"""
    with v_gen() as gen:
        with v_module("fifo_system"):
            # 参数
            v_param("DATA_WIDTH", "32")
            v_param("FIFO_DEPTH", "16")
            
            # 端口
            v_input("clk")
            v_input("rst_n")
            v_input("start")
            v_input("test_data", "DATA_WIDTH")
            v_output("output_data", "DATA_WIDTH", None, "wire")
            v_output("system_error", 1, None, "wire")
            v_output("fifo_count", "$clog2(FIFO_DEPTH)+1", None, "wire")
            
            # 内部信号
            v_wire("fifo_full")
            v_wire("fifo_empty")
            v_wire("wr_enable") 
            v_wire("rd_enable")
            
            v_newline()
            v_body("// FIFO 实例化")
            v_inst("sync_fifo", "u_fifo",
                   {"DATA_WIDTH": "DATA_WIDTH", "FIFO_DEPTH": "FIFO_DEPTH"},
                   {
                       "clk": "clk",
                       "rst_n": "rst_n",
                       "wr_en": "wr_enable",
                       "rd_en": "rd_enable",
                       "wr_data": "test_data",
                       "rd_data": "output_data",
                       "full": "fifo_full",
                       "empty": "fifo_empty",
                       "count": "fifo_count"
                   })
            
            v_newline()
            v_body("// 控制器实例化")
            v_inst("fifo_controller", "u_controller",
                   {},
                   {
                       "clk": "clk",
                       "rst_n": "rst_n", 
                       "start": "start",
                       "fifo_full": "fifo_full",
                       "fifo_empty": "fifo_empty",
                       "wr_en": "wr_enable",
                       "rd_en": "rd_enable",
                       "error": "system_error"
                   })
    
    return gen.generate()


def main():
    """主函数"""
    print("=== 生成 FIFO 系统模块 ===")
    
    # 生成 FIFO 模块
    fifo_code = generate_fifo()
    with open("sync_fifo.sv", "w") as f:
        f.write(fifo_code)
    print("生成了 sync_fifo.sv")
    
    # 生成状态机控制器
    controller_code = generate_state_machine() 
    with open("fifo_controller.sv", "w") as f:
        f.write(controller_code)
    print("生成了 fifo_controller.sv")
    
    # 生成顶层模块
    top_code = generate_top_module()
    with open("fifo_system.sv", "w") as f:
        f.write(top_code)
    print("生成了 fifo_system.sv")
    
    print("✅ FIFO 系统生成完成!")
    print("\n生成的文件:")
    print("- sync_fifo.sv: 参数化同步FIFO")
    print("- fifo_controller.sv: 状态机控制器") 
    print("- fifo_system.sv: 顶层集成模块")


if __name__ == "__main__":
    main()