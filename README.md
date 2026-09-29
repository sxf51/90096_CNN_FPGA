# SRCNN 超分辨率推理（Vitis HLS）

本项目用 C++ 实现三层 SRCNN 网络，并以 `srcnn` 作为 Vitis HLS 的综合顶层函数。代码读取预训练权重，对单通道、255 × 255 的输入图像进行推理，输出同尺寸的重建图像。`UP=3` 表示测试数据对应的 3 倍超分辨率任务；输入文件已经具有 255 × 255 的尺寸，网络本身不再改变宽高。

## 网络结构

| 层 | 输入通道 | 输出通道 | 卷积核 | 激活 |
| --- | ---: | ---: | ---: | --- |
| Conv1 | 1 | 64 | 9 × 9 | ReLU |
| Conv2 | 64 | 32 | 1 × 1 | ReLU |
| Conv3 | 32 | 1 | 5 × 5 | 无 |

卷积采用步长 1。Conv1 和 Conv3 在边界外重复最近的边缘像素，使各层特征图保持 255 × 255。权重和偏置为单精度浮点数；当前代码负责推理，不包含模型训练或图像插值步骤。

## 文件说明

| 路径 | 用途 |
| --- | --- |
| `src/srcnn.h` | 图像尺寸、网络参数、数据类型和函数声明 |
| `src/conv1.cpp` | 第一层卷积与 ReLU |
| `src/srcnn.cpp` | 顶层函数，依次执行三层网络 |
| `src/weights/` | 三层网络的预训练权重和偏置 |
| `test/tb_conv1.cpp` | 第一层输出与 golden 数据的 MSE 比较 |
| `test/tb_srcnn.cpp` | 完整网络输出与 golden 数据的 MSE 比较 |
| `test/tb_set14.cpp` | Set14 图像的 MSE、PSNR 评估；默认未启用 |
| `test/set5/`、`test/set14/` | 输入图像、真值图像及参考数据 |
| `script.py` | 创建 Vitis HLS 组件及配置 |
| `workspace/` | Vitis 生成的工作区，已被 `.gitignore` 忽略 |

## 在 Vitis 中运行 C 仿真

1. 安装 Vitis 2026.1，并确认安装目录。
2. 打开 Windows **命令提示符（CMD）**，进入项目根目录，依次运行：

   ```bat
   chcp 65001
   call "<你安装Vitis的地方>\AMDDesignTools\2026.1\Vitis\settings64.bat"
   vitis -s script.py
   ```

   将 `<你安装Vitis的地方>` 替换为实际安装路径的前缀。`chcp 65001` 将控制台切换为 UTF-8，避免中文输出乱码；`call` 加载 Vitis 环境并返回当前 CMD 窗口，使下一条命令可以继续执行。

   **注意：**脚本每次运行都会删除并重建项目根目录下的 `workspace/`。如有需要保留的工作区内容，请先移出该目录。

3. 脚本结束后关闭该命令行窗口，在 Vitis GUI 中将工作区设为项目的 `workspace/`，打开 `baseline` 组件，运行 **C Simulation**。

配置文件位于 `workspace/baseline/hls_config.cfg`。目标器件为 `xck26-sfvc784-2LV-c`，目标时钟为 10 ns。C 仿真通过只表示功能结果得到验证；资源占用、时序和实际硬件性能需要另行运行 HLS 综合检查。

默认入口 `test/csim.cpp` 调用 Conv1 和完整网络的测试。若要运行 Set14 测试，按文件中的提示启用 `tb_set14()`。测试程序通过相对路径读取 `./weights/` 和 `./set5/` 等数据；Vitis 组件配置已把这些目录加入测试文件。

## 验证结果

使用项目提供的 butterfly 输入、权重及 golden 输出进行本地 C++ 对比，得到：

| 输出 | 与 golden 数据的 MSE |
| --- | ---: |
| Conv1 | 约 3.46 × 10⁻¹⁵ |
| 完整 SRCNN | 约 3.17 × 10⁻¹⁴ |

这些数值反映单精度计算与参考输出基本一致；它们不是与高分辨率真值图像比较的超分辨率质量指标。图像质量可通过 Set14 测试中的 MSE 和 PSNR 评估。

## 参考

- [sharc-lab FPGA_ECE8893 Lab2](https://github.com/sharc-lab/FPGA_ECE8893/tree/main/2023_Spring/Lab2)：卷积及 HLS 实现方法参考。该 Lab2 的网络与本项目的三层 SRCNN 不相同。
