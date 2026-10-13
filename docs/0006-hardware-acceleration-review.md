# SRCNN 硬件加速效果与下一步优化（汇报记录）

## 已验证的当前实现
当前上板设计是src/的16×16分块float32实现，不是图中F25的w10a10acc23流式架构。
Butterfly板端MSE=3.1660971422452726e-14，maxerr=9.5367431640625e-7；与C仿真MSE一致。
重复调用输出完全相同；偏置更新最大误差5.364418029785156e-7。
13张Set14平均截幅浮点PSNR=29.1587233dB；输入27.5888614dB，平均提高1.5698619dB。
这证明算法在板端运行正确；没有相同输入/精度/算法的CPU实测，不能声称对CPU的加速比。

14张图（butterfly+13张Set14）平均板端轮询耗时2.2375389066s，约0.447FPS。
Clocks读取PL0为66.666MHz；HWH设计频率99.999001MHz；HLS周期147849536在运行时钟下为2.2177652177s。
差额19.773689ms，占实测0.8837%，不能单独归因DDR。HLS本身已有模型化访存调度。
时钟读数是寄存器推算，不是仪器测量。见0005诊断记录。

## 架构效果与资源证据
冻结原始HLS基线BRAM18K=11064，对288容量不成立；分块float HLS=151，降98.635%。
原版4482223011周期，当前147849536周期，同100MHz下44.822s到1.478s，周期改善30.316倍。
这是两个HLS模型比较，原版不能放入器件，不是CPU/真实旧硬件速度比。
消除完整中间特征，代价是块边halo重算：522280800 MAC增加至792985600 MAC，增加51.83%。
完整PS+SRCNN+互连系统placed报告：LUT10296/117120=8.79%，FF15727/234240=6.71%，DSP46/1248=3.69%，BRAM72.5/144=50.35%。
不要混用独立IP6940 LUT与系统资源。系统routed时序WNS+3.648ns、TNS0，WHS+0.010ns、THS0，已生成bitstream。

## 分层瓶颈
srcnn_csynth.rpt每块first=266693周期，Conv2=105713，Conv3=204819；块总577497。
约46.18%/18.31%/35.47%，为HLS模块估计归因，不是板端分层计数。
内部计算循环II1不等于整网逐像素持续输出；当前三层和块仍顺序执行。
只优化Conv1，理想无限加速上限约1/(1-.4618)=1.86倍；只优化Conv3上限约1.55倍。

## 优化优先级
1. 恢复实际PL0至100MHz并复测，预计约1.492s，潜在约1.5倍。先检查idle、只调整PL0、复查golden；尚未做修改。
2. 提高Conv1输出通道并行度及Conv3像素/乘加并行度；DSP占用很低，但BRAM约一半，必须逐个扫描并依据实际综合/route留余量。不能按DSP余额线性推断加速。
3. 可选INT8已有完整尺寸Csim/HLS与17×17两帧RTL PASS。HLS60967603周期、0.610s@100MHz，BRAM96 DSP112 LUT31608；与当前float估计2.43倍，未完成INT8板端/完整尺寸RTL验收。平均PSNR下降0.644dB，最差2.470dB，应按质量目标决定。
4. 更值得探索10位定点+整网流式行缓存。F25 DSP502/BRAM73/LUT69976/FF125404；LUT59.75%、FF53.54%，高于当前系统。F80全部13图相对自己的float参照平均下降0.069514dB；并非浮点bit-exact。
   F82 RTL两帧PASS，单帧1068183周期；HLS1056904周期。2.64226ms来自400MHz目标，不是板端成绩，且HLS时钟不确定度警告仍须route解决。即便只按100MHz除RTL周期约10.682ms，仍只是周期换算，不是实际系统保证。F81实现因host OOM失败，没有routed证据；OOM不等于设计逻辑超限。需独立冻结源码/寄存器/测试重新实现和上板。
5. 对当前float，DDR分口和双缓冲为次级：多余19.8ms只占0.88%，不能期待仅靠消除额外等待获得大幅提升，也不能说所有访存仅0.88%。流式和更快算术后总线可能变主瓶颈。
6. Winograd/packing只作为后续：C11虽然估计1.0817ms，但LUT248797/FF307525均超器件容量。最短估计不等于可部署方案。

## 必备后续测量
相同算法和输入的CPU基准（区分朴素C++/优化库）；实际PL频率记录；AP_START/AP_DONE硬件周期计数；
AXI Performance Monitor的字节/拍/事务/等待统计；每个候选routed时序与资源；原始和截幅PSNR、边界、参数更新、所有数据。

## 证据索引
- 板端：http://kria-22:9090/notebooks/90096_hls/srcnn_hls.ipynb （已保存运行输出与时钟诊断）
- validation/kv260/synthesis_summary.json；reports/baseline,float,int8/
- workspace/baseline/baseline/hls/syn/report/srcnn_csynth.rpt
- project/project.runs/impl_1/design_1_wrapper_utilization_placed.rpt
- project/project.runs/impl_1/design_1_wrapper_timing_summary_routed.rpt
- experiments/F80_final_all_supplied_F25/config.json：定点精度
- experiments/F82_final_cosim_F25/config.json：RTL
- experiments/F81_final_impl_F25/config.json：OOM/缺route
- experiments/ARCH_SUMMARY.md：超限与失败案例
