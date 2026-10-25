# HLS 报告位置与 Git 保留规则

## 问题与现状

原 `.gitignore` 使用 `/workspace/` 排除整个 Vitis 工作区，并使用 `*.log` 排除日志。即使其中生成了有价值的仿真或综合报告，Git 也看不到它们。

参考 `../../w4/genshin_start_hls`：其已有记录保留了 `syn/report/` 下的 `csynth.rpt`、`csynth.xml`、`fir_csynth.rpt` 等，同时忽略生成 HDL 和编译中间文件，并将选定实验报告复制到 `output/`。

本项目当前没有生成 `workspace/` 或综合报告。以下路径根据相同 Vitis 2026.1 创建脚本在 `golden` 项目中的实际目录，以及 w4 的综合报告目录确定；不能把其他项目的数值当成本项目的验证结果。

## 报告与指标

当前 GUI 流程通常在 `workspace/baseline/baseline/` 下生成运行结果。以下相对路径均从项目根目录开始：

| 文件 | 主要内容 |
| --- | --- |
| `workspace/baseline/baseline/hls/csim/report/srcnn_csim.log` | testbench 输出、MSE、编译与 C 仿真成功或失败信息 |
| `workspace/baseline/baseline/logs/hls_run_csim.log` | C 仿真完整工具日志；结尾的 CPU 时间、Total elapsed time、内存等 |
| `workspace/baseline/baseline/hls/syn/report/csynth.rpt` | 综合摘要：模块及循环延迟、周期数、II、时序估计或 Slack、资源估计 |
| `workspace/baseline/baseline/hls/syn/report/srcnn_csynth.rpt` | 顶层综合详细报告；具体栏目随工具版本变化 |
| `workspace/baseline/baseline/hls/syn/report/*.xml` | 综合指标的机器可读版本，便于后续比较与汇总 |
| `workspace/baseline/baseline/logs/hls_run_synth.log` | 综合过程、警告和工具运行耗时；运行后确认实际生成的文件名 |
| `workspace/baseline/baseline/hls/sim/report/srcnn_cosim.rpt` | C/RTL 协同仿真结果，以及该次仿真测得的 RTL 延迟和间隔 |
| `workspace/baseline/baseline/hls/impl/report/` 下的 `.rpt`、`.xml` | 导出或实现报告，按实际执行的步骤确认是否包含实现后的时序和资源 |

使用 `vitis-run --work_dir <目录>` 时，前缀由 `<目录>` 决定；例如独立任务可生成 `build/vscode-hls/hls/syn/report/`。不同版本或流程的目录层级可能变化，识别 `syn/report`、`csim/report` 等后缀即可。

在 Linux 或 macOS 项目根目录查找已生成的结果：

```sh
find workspace build -type f \( -name '*csynth*.rpt' -o -name '*csynth*.xml' -o -name '*_csim.log' -o -name '*_cosim.rpt' -o -name 'hls_run_*.log' \) -print
```

只传入实际存在的目录，避免 `find` 提示目录不存在。

### 三种时间的区别

- **工具运行耗时**：日志中的 `Total elapsed time`，表示电脑执行仿真或综合花了多久，不是 FPGA 推理耗时。
- **硬件延迟估计**：综合报告中的 `Latency (cycles)` 及时间估计。若按 10 ns 时钟运行，100,000 周期对应 1 ms；这仍不是板端实测。
- **流水线启动间隔**：`Interval` / `II` 表示连续启动计算的间隔，不能与一次计算的总延迟混淆。

综合报告中的目标时钟、估计时序或 Slack 也不代表布局布线后的实际可达频率。最终时序查看 Vivado 实现后的 timing summary；端到端速度还需计入接口、数据传输和主机调用，并在板上测量。

当前 testbench 只打印 MSE，未按阈值判定失败；`CSim done with 0 errors` 不能替代对实际 MSE 的检查。

## Git 保留方案

- 将 `/workspace/` 的整体排除改为默认排除其中的文件，并允许 Git 遍历目录，以便明确放行报告。
- 对 `/build/` 使用同样的规则，覆盖独立 HLS 命令的输出目录。
- 保留 `syn/report/`、`sim/report/`、`impl/report/` 下的 `.rpt` 和 `.xml`，以及 `csim/report/*_csim.log`。
- 保留选定的 `logs/hls_run_csim.log`、`logs/hls_run_synth.log`、`logs/hls_run_cosim.log`，用于查看工具运行耗时和警告。
- 保留 `hls_config.cfg`，便于核对顶层函数、器件、目标时钟和综合设置。
- 继续排除 IDE 状态、缓存、生成 HDL、仿真程序、波形、编译文件及其他未选定的工作区文件。
- `output/<实验名>/` 用于主动归档的结果；其中复制的 `.log` 也允许跟踪。每份归档应附对应源码提交、工具版本、配置、误差指标和关键警告。
- `AGENTS.md` 继续由各副本的 `.git/info/exclude` 排除，不能上传 GitHub。

规则文件不生成报告，也不自动暂存或上传报告。报告生成后仍需检查内容，再选择要提交的文件。

## 结果保护与失败模式

`script.py` 每次运行仍会删除并重建 `workspace/`。Git 不再忽略某些报告，并不能防止文件被脚本删除或下次运行覆盖。重要结果先复制到 `output/<实验名>/`，再按需提交；不要把唯一一份未提交的实验报告留在工作区。

Vitis 可能生成子目录 `.gitignore`，其规则可以覆盖根目录的规则。若预期报告仍被忽略，用 `git check-ignore -v <报告路径>` 确认原因；需要归档时可将选定报告复制到 `output/`，不依赖生成目录中的规则。

本次修改只改变版本控制规则和说明，不运行 HLS、不复制其他项目的结果、不改变算法、器件或时钟配置。

## 验收

1. 仿真结果、综合 `.rpt`/`.xml`、选定运行日志和 HLS 配置不被根目录规则排除。
2. 覆盖 GUI 的双层 `baseline` 路径、不同组件名称，以及 `build/vscode-hls` 路径。
3. 缓存、生成 HDL、仿真可执行文件、波形和未选定工作区文件仍被排除。
4. `output/` 中主动归档的结果日志可以跟踪，普通临时日志仍被排除。
5. 本地及远程副本都排除 `AGENTS.md`；不进行 GitHub 推送。

## 验证记录（2026-10-10）

- 在独立临时 Git 仓库中创建 81 个实际文件，用 `git ls-files --others --exclude-standard` 检查其可见性：41 个报告、配置及归档路径允许跟踪，40 个产物或本地规则路径被排除，全部符合预期。
- 覆盖双层 `baseline`、不同组件名、`build/vscode-hls`、子目录综合报告及实现报告，同时加入 w4 的 Vitis 自动生成 `.gitignore` 验证当前 GUI 路径。
- 缓存中名称类似综合报告的文件、备份日志、生成 HDL、仿真程序和普通日志仍被排除；`output/` 中主动归档的日志允许跟踪。
- `git diff --check` 通过；`git check-ignore -v` 确认本地 `AGENTS.md` 和 `agent.md` 仍由 `.git/info/exclude` 排除。
- 修改位于 `feature/preserve-hls-reports` 分支；未运行 HLS，因此没有本项目的新延迟、资源或时序数值。
