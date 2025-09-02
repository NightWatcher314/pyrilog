#!/usr/bin/env python3
"""
示例1: 简单的 ALU 设计
演示 case 语句的单语句和多语句用法
"""

from pyrilog import *


def generate_simple_alu():
    """生成简单的 ALU 模块"""
    with v_gen() as gen:
        with v_module("simple_alu"):
            # 参数定义
            v_param("DATA_WIDTH", "8")
            
            # 端口定义
            v_input("clk")
            v_input("rst_n")
            v_input("opcode", 3)
            v_input("a", "DATA_WIDTH")
            v_input("b", "DATA_WIDTH") 
            v_output("result", "DATA_WIDTH", None, "reg")
            v_output("valid", 1, None, "reg")
            
            # 时序逻辑
            with v_always_ff("clk", "rst_n"):
                with v_if("!rst_n"):
                    v_body("result <= {DATA_WIDTH{1'b0}};")
                    v_body("valid <= 1'b0;")
                with v_else():
                    with v_case("opcode"):
                        # 单语句 case 项
                        v_case_item("3'b000", "result <= a + b;")        # 加法
                        v_case_item("3'b001", "result <= a - b;")        # 减法
                        v_case_item("3'b010", "result <= a & b;")        # 按位与
                        v_case_item("3'b011", "result <= a | b;")        # 按位或
                        v_case_item("3'b100", "result <= a ^ b;")        # 按位异或
                        
                        # 多语句 case 项 - 左移操作，带溢出检测
                        with v_case_item("3'b101"):
                            v_body("result <= a << 1;")
                            v_body("if (a[DATA_WIDTH-1]) valid <= 1'b0; // 溢出")
                            v_body("else valid <= 1'b1;")
                        
                        # 多语句 case 项 - 右移操作
                        with v_case_item("3'b110"):
                            v_body("result <= a >> 1;")
                            v_body("valid <= 1'b1;")
                        
                        # 默认情况
                        v_case_default("result <= {DATA_WIDTH{1'b0}};")
                    
                    # case 块外的公共逻辑
                    v_body("if (opcode != 3'b101) valid <= 1'b1;")
    
    return gen.generate()


def generate_counter():
    """生成一个简单的计数器模块"""  
    with v_gen() as gen:
        with v_module("counter"):
            v_param("WIDTH", "8")
            
            v_input("clk")
            v_input("rst_n")
            v_input("en")
            v_output("count", "WIDTH", None, "reg")
            v_output("overflow", 1, None, "reg")
            
            with v_always_ff("clk", "rst_n"):
                with v_if("!rst_n"):
                    v_body("count <= {WIDTH{1'b0}};")
                    v_body("overflow <= 1'b0;")
                with v_else():
                    with v_if("en"):
                        v_body("if (count == {WIDTH{1'b1}}) begin")
                        v_body("    count <= {WIDTH{1'b0}};")
                        v_body("    overflow <= 1'b1;")
                        v_body("end else begin")
                        v_body("    count <= count + 1'b1;")
                        v_body("    overflow <= 1'b0;")
                        v_body("end")
    
    return gen.generate()


def main():
    """主函数"""
    print("=== 生成示例模块 ===")
    
    # 生成 ALU
    alu_code = generate_simple_alu()
    with open("simple_alu.sv", "w") as f:
        f.write(alu_code)
    print("生成了 simple_alu.sv")
    
    # 生成计数器  
    counter_code = generate_counter()
    with open("counter.sv", "w") as f:
        f.write(counter_code)
    print("生成了 counter.sv")
    
    print("✅ 所有模块生成完成!")


if __name__ == "__main__":
    main()