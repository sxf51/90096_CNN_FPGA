# frozen_string_literal: true

require "csv"
require "json"
require "pathname"

OUT = Pathname.new(__dir__)
ROOT = OUT.parent.parent
CATALOG = JSON.parse((OUT / "catalog.json").read)
BUDGET = { "DSP" => 1248, "BRAM18K" => 288, "URAM" => 64,
           "LUT" => 81984, "FF" => 163968 }.freeze
HLS_FIELDS = %w[clock_target_ns clock_est_ns latency_cycles interval_cycles
                latency_ms_est DSP BRAM18K URAM LUT FF ii_ok].freeze
FUNCTIONAL_FIELDS = %w[csim_pass bit_exact butterfly_mse border_mse].freeze
STATUS = { "infeasible" => "资源/性能门槛未满足", "analysis_complete" => "分析完成",
           "fail" => "运行失败", "invalid_config" => "配置无效", "timeout" => "超时",
           "csim_pass" => "C 仿真通过", "provisional" => "候选，仍需验收",
           "impl_complete" => "实现完成，另看时序", "pass" => "局部实验通过",
           "cosim_complete" => "RTL 协仿完成", "planned" => "已准备，未归档测量" }.freeze

def read_json(path)
  path.file? ? JSON.parse(path.read) : {}
end

def typed(value)
  return nil if value.nil? || value == ""
  return true if value == "True"
  return false if value == "False"
  return value unless value.match?(/\A-?\d+(?:\.\d+)?(?:e[+-]?\d+)?\z/i)

  number = Float(value)
  number == number.to_i ? number.to_i : number
end

def number(value, decimals = 4)
  return "未知" if value.nil?
  return value.to_i.to_s if value == value.to_i

  format("%.#{decimals}f", value).sub(/0+\z/, "").sub(/\.\z/, "")
end

def relative(path)
  Pathname.new(path).relative_path_from(ROOT).to_s
end

def link(path, label = nil)
  target = (ROOT / path).relative_path_from(OUT).to_s
  "[#{label || path}](#{target})"
end

rows = CSV.read(ROOT / "experiments/results.csv", headers: true).map(&:to_h)
row_by_id = rows.to_h { |row| [row.fetch("id"), row] }
plans = Dir[ROOT / "exp/configs/*.json"].to_h do |path|
  [File.basename(path, ".json"), read_json(Pathname.new(path))]
end
workflow = read_json(ROOT / "experiments/rom_clock_state.json")
curated = CATALOG.fetch("sections").flat_map { |section| section.fetch("records") }
ids = curated.map(&:first)
expected = row_by_id.keys | plans.keys
abort "Duplicate IDs" unless ids.uniq.size == ids.size
abort "Catalog coverage differs: #{(expected - ids).inspect} / #{(ids - expected).inspect}" unless ids.sort == expected.sort
known_edges = CATALOG.fetch("edge_kinds")
curated.each do |id, _, parents, _, _|
  parents.each do |parent, kind|
    abort "#{id}: unknown parent #{parent}" unless ids.include?(parent)
    abort "#{id}: unknown relation #{kind}" unless known_edges.key?(kind)
  end
end
CATALOG.fetch("sections").each do |section|
  section.fetch("evidence").each do |path|
    abort "Missing evidence: #{path}" unless (ROOT / path).exist?
  end
end
lookup = curated.to_h { |row| [row[0], row] }
visiting = {}
visited = {}
visit = lambda do |id|
  abort "Dependency cycle at #{id}" if visiting[id]
  next if visited[id]

  visiting[id] = true
  lookup.fetch(id)[2].each { |parent, _| visit.call(parent) }
  visiting.delete(id)
  visited[id] = true
end
ids.each { |id| visit.call(id) }

records = CATALOG.fetch("sections").flat_map do |section|
  section.fetch("records").map do |id, title, parents, change, issue|
    raw = row_by_id[id]
    metrics = (raw || {}).transform_values { |value| typed(value) }
    archive = raw && ROOT / "experiments" / File.dirname(raw.fetch("md_path"))
    cfg = archive ? read_json(archive / "config.json") : plans.fetch(id)
    operation = cfg["operation"]
    verification_run = %w[impl cosim].include?(operation)
    scope = cfg["scope"] || case id
                             when /\AE05[1-5]\z/ then "PE"
                             when "E049" then "boundary"
                             when "E010", "E062", "E071" then "analysis"
                             else "frame"
                             end
    hls = if raw && !verification_run && metrics["latency_cycles"]
            metrics.slice(*HLS_FIELDS)
          end
    if hls
      hls["time_basis_ns"] = [hls["clock_target_ns"], hls["clock_est_ns"]].compact.max
      expected_ms = hls["latency_cycles"] * hls["time_basis_ns"] / 1e6
      abort "#{id}: unexpected HLS time conversion" if (expected_ms - hls["latency_ms_est"]).abs > 1e-8
    end
    functional = if raw && !verification_run
                   metrics.slice(*FUNCTIONAL_FIELDS)
                 end
    quality = if raw && !verification_run && metrics["set14_psnr"]
                {
                  "psnr_gt_db" => metrics["set14_psnr"],
                  "delta_vs_float_db" => metrics["delta_psnr"],
                  "provenance" => cfg["quality_provenance"] || {
                    "method" => "本次仿真；逐图范围见原始验证记录",
                    "image_count" => cfg.dig("validation", "image_count")
                  }
                }
              end
    measured_verification = archive ? read_json(archive / "verification.json") : {}
    measured_verification = cfg["verification"] || {} if measured_verification.empty?
    timing = []
    synth_log = archive && archive / "csynth.log.txt"
    if hls && synth_log.file?
      synth_log.each_line.with_index(1) do |line, line_number|
        next unless line.include?("WARNING: [HLS 200-871]")

        values = line.scan(/([\d.]+) ns/).flatten.map(&:to_f)
        entry = { "estimated_ns" => values[0], "target_ns" => values[1],
                  "uncertainty_ns" => values[2], "effective_budget_ns" => values[3],
                  "log_line" => line_number }
        timing << entry unless timing.any? { |existing| existing.slice("estimated_ns", "target_ns", "uncertainty_ns", "effective_budget_ns") == entry.slice("estimated_ns", "target_ns", "uncertainty_ns", "effective_budget_ns") }
      end
    end
    exceeded = hls ? BUDGET.select { |field, limit| hls[field] && hls[field] > limit }.keys : []
    status = raw ? raw.fetch("status") : "planned"
    execution_state = !raw && workflow.fetch("experiment_ids", []).include?(id) ? "queued_or_running" : nil
    flags = []
    flags << "未归档测量" unless raw
    flags << "超预算: #{exceeded.join('/')}" unless exceeded.empty?
    flags << "II 未达目标" if hls && hls["ii_ok"] == false
    flags << "HLS 时序警告" unless timing.empty?
    flags << "配置无效" if status == "invalid_config"
    flags << "主机 OOM" if cfg.dig("host_failure", "kind") == "kernel_oom"
    flags << "主机内存保护中止" if cfg.fetch("errors", []).any? { |error| error.include?("MemAvailable floor") }
    flags << "原周期门限失败；后获用户授权" if cfg["acceptance_override"]
    flags << "实现时序未达标" if measured_verification["timing_met"] == false
    flags << "仅诊断，沿用父设计 HLS 门槛" if cfg["diagnostic_infeasible_parent"]
    paths = []
    paths << relative(ROOT / "exp/configs/#{id}.json") if plans.key?(id)
    if archive
      paths << "experiments/#{raw.fetch('md_path')}"
      %w[config.json metrics.json verification.json csynth.rpt csynth.log.txt
         csim.log.txt impl.log.txt cosim.log.txt diagnostics/kernel_oom.txt
         primitive_probe.json dsp_primitives.csv reports/sim/srcnn_cosim.rpt].each do |name|
        paths << relative(archive / name) if (archive / name).file?
      end
      Dir[archive / "reports/impl/*routed.rpt"].sort.each { |path| paths << relative(path) }
    end
    paths.each { |path| abort "Missing record evidence: #{path}" unless (ROOT / path).file? }
    run_kind = if !raw
                 "plan"
               elsif verification_run
                 operation
               elsif hls
                 "csim_csynth"
               elsif status == "analysis_complete"
                 "analysis"
               else
                 "csim"
               end
    tone = if status == "planned"
             "planned"
           elsif %w[fail timeout invalid_config].include?(status) || flags.include?("实现时序未达标")
             "failure"
           elsif !exceeded.empty? || (hls && hls["ii_ok"] == false) || cfg["diagnostic_infeasible_parent"]
             "infeasible"
           elsif !timing.empty?
             "warning"
           elsif run_kind == "analysis"
             "analysis"
           else
             "candidate"
           end
    graph_result = if execution_state
                     "已排队/运行，暂无归档测量"
                   elsif operation == "cosim" && raw
                     "RTL #{measured_verification['rtl_status'] || '未完成'} / #{number(measured_verification['rtl_latency_max'])} cycles"
                   elsif operation == "impl" && raw
                     if measured_verification.key?("impl_WNS_ns")
                       "Routed WNS #{number(measured_verification['impl_WNS_ns'])} ns"
                     elsif flags.include?("主机 OOM")
                       "主机 OOM；无 routed 结果"
                     else
                       "物理实现未完成"
                     end
                   elsif hls && scope == "frame"
                     "HLS 估计 #{number(hls['latency_ms_est'])} ms / DSP #{number(hls['DSP'])}"
                   elsif hls
                     "#{scope == 'layer' ? '单层' : 'PE'}: DSP #{number(hls['DSP'])} / LUT #{number(hls['LUT'])}"
                   elsif quality
                     "C 仿真 / 平均 ΔPSNR #{number(quality['delta_vs_float_db'])} dB"
                   else
                     STATUS.fetch(status, status)
                   end
    graph_flags = flags.empty? ? STATUS.fetch(status, status) : flags.join("；")
    graph_flags = "独立布线门限通过" if measured_verification["route_feasible"] == true && flags.empty?
    {
      "id" => id, "section" => section.fetch("key"), "title" => title,
      "parents" => parents.map { |parent, kind| { "id" => parent, "kind" => kind } },
      "change" => change, "issue" => issue, "has_result_record" => !raw.nil?,
      "status" => status, "scope" => scope, "run_kind" => run_kind,
      "execution_state" => execution_state,
      "resource_policy" => cfg["resource_policy"],
      "acceptance_override" => cfg["acceptance_override"],
      "source_commit" => cfg["source_commit"] || metrics["git_commit"],
      "tool_version" => cfg["tool_version"]&.match(/vitis-run v(\d+\.\d+)/)&.captures&.first,
      "hls" => hls, "functional" => functional, "quality" => quality,
      "verification" => measured_verification,
      "diagnostic_only" => cfg["diagnostic_infeasible_parent"] == true,
      "inherited_hls_parent" => verification_run ? cfg["verify_parent"] : nil,
      "hls_timing_warnings" => timing, "flags" => flags,
      "errors" => raw ? cfg.fetch("errors", []) : [],
      "evidence" => paths, "registry_raw" => raw,
      "planned_estimates" => raw ? nil : cfg["estimates"],
      "graph" => { "result" => graph_result, "flags" => graph_flags, "tone" => tone }
    }
  end
end

data = {
  "schema_version" => 1, "source_commit" => CATALOG.fetch("source_commit"),
  "counts" => { "experiments" => records.size, "with_result_record" => rows.size,
                "plan_only" => records.count { |record| !record["has_result_record"] } },
  "resource_budget" => BUDGET, "edge_kinds" => known_edges,
  "sections" => CATALOG.fetch("sections").map { |section| section.reject { |key, _| key == "records" } },
  "records" => records
}
(OUT / "data.json").write(JSON.pretty_generate(data) + "\n")

lines = ["# 全部实验：来源、调整、效果与问题", "", "[English](records.en.md)", "",
         "快照：`#{CATALOG.fetch('source_commit')}`；#{records.size} 项，#{rows.size} 项有结果档案，#{data['counts']['plan_only']} 项仅有计划/准备。", "",
         "有结果档案包括失败、超时和无效配置，不表示全部成功。箭头表示设计、参数、模块与验收依赖，不能当成逐次 Git clone 历史。", "",
         "HLS 时间沿用注册表公式：cycles × max(目标周期, HLS 估计周期) / 10⁶ ms。这个估计不证明 uncertainty 后时序达标，也不是板端测量。资源预算为 DSP≤1248、BRAM18K≤288、URAM≤64、LUT≤81984、FF≤163968；后两项是全芯片容量的 70%。", "",
         "普通综合记录的多图质量可能引用独立精度参考；下方会标出来源。本次逐图验收范围以原始配置的 image_count 为准。实现/RTL 记录继承的 HLS 指标只保存在 data.json 的 registry_raw，展示时使用该步骤的真实测量。", "",
         "[返回说明](../0004-experiment-evolution.md) · [总览图](overview.svg) · [机器可读数据](data.json)", "",
         "## 路线索引", "", "| 路线 | 编号 | |", "| --- | --- | --- |"]
CATALOG.fetch("sections").each do |section|
  record_links = section.fetch("records").map { |row| "[#{row[0]}](##{row[0].downcase})" }.join(" ")
  lines << "| [#{section['title']}](##{section['key']}) | #{record_links} | [图](#{section['key']}.svg) |"
end
by_id = records.to_h { |record| [record["id"], record] }
CATALOG.fetch("sections").each do |section|
  lines += ["", "<a id=\"#{section['key']}\"></a>", "", "## #{section['title']}", "",
            section.fetch("question"), "", "[演进图](#{section['key']}.svg)；路线依据：#{section['evidence'].map { |path| link(path) }.join(' · ')}。"]
  section.fetch("records").each do |row|
    record = by_id.fetch(row[0])
    lines += ["", "<a id=\"#{record['id'].downcase}\"></a>", "", "### #{record['id']}：#{record['title']}", ""]
    parents = record["parents"].map { |parent| "[#{parent['id']}](##{parent['id'].downcase})（#{known_edges.fetch(parent['kind'])}）" }
    lines << "**基于：** #{parents.empty? ? '原始 src/ 基线，没有前置实验。' : parents.join('；') + '。'}"
    lines += ["", "**调整：** #{record['change']}", "", "**效果与问题：** #{record['issue']}", ""]
    lines << "**记录状态：** `#{record['status']}` / #{STATUS.fetch(record['status'])}；范围 `#{record['scope']}`；步骤 `#{record['run_kind']}`。"
    lines << "附加检查：#{record['flags'].join('；')}。" unless record["flags"].empty?
    hls = record["hls"]
    if hls
      lines += ["", "| HLS 测量/估计 | 值 |", "| --- | --- |",
                "| 目标周期 / 估计周期 | #{number(hls['clock_target_ns'])} / #{number(hls['clock_est_ns'])} ns |",
                "| 延迟 / 间隔 | #{number(hls['latency_cycles'])} / #{number(hls['interval_cycles'])} cycles |",
                "| 注册表换算时间 | #{number(hls['latency_ms_est'], 8)} ms（#{record['scope']} 范围，以 #{number(hls['time_basis_ns'])} ns 换算） |",
                "| DSP / BRAM18K / URAM | #{number(hls['DSP'])} / #{number(hls['BRAM18K'])} / #{number(hls['URAM'])} |",
                "| LUT / FF | #{number(hls['LUT'])} / #{number(hls['FF'])} |",
                "| 所检查的 II 目标 | #{hls['ii_ok'].nil? ? '未记录' : hls['ii_ok'] ? '达到' : '未达到'} |"]
    end
    warnings = record["hls_timing_warnings"]
    unless warnings.empty?
      worst = warnings.max_by { |warning| warning["estimated_ns"] || 0 }
      lines += ["", "HLS 200-871：逻辑预算 #{number(worst['target_ns'])} − #{number(worst['uncertainty_ns'])} = #{number(worst['effective_budget_ns'])} ns；告警路径最高估计 #{number(worst['estimated_ns'])} ns。详见原始综合日志。"]
    end
    functional = record["functional"]
    if functional && functional["csim_pass"]
      values = ["C 仿真通过", "bit_exact=#{functional['bit_exact'].nil? ? '未记录' : functional['bit_exact']}"]
      values << "butterfly MSE=#{functional['butterfly_mse']}" if functional["butterfly_mse"]
      values << "六像素边界 MSE=#{functional['border_mse']}" if functional["border_mse"]
      lines += ["", "功能：#{values.join('；')}。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。"]
    end
    quality = record["quality"]
    if quality
      provenance = quality.fetch("provenance")
      origin = provenance["path"] ? link(provenance["path"]) : "本次仿真（#{provenance['image_count'] || '数量未单列'} 张；见原始记录）"
      lines += ["", "质量：对 GT 的平均 PSNR=#{number(quality['psnr_gt_db'], 6)} dB；相对浮点平均 ΔPSNR=#{number(quality['delta_vs_float_db'], 6)} dB。来源：#{origin}。"]
    end
    verification = record["verification"]
    if record["inherited_hls_parent"]
      lines += ["", "继承的 HLS 估计来自 [#{record['inherited_hls_parent']}](##{record['inherited_hls_parent'].downcase})，不作为本步骤的新测量。"]
    end
    if verification.key?("rtl_status")
      lines += ["", "RTL：#{verification['rtl_status']}；最大延迟 #{number(verification['rtl_latency_max'])} cycles；最大间隔 #{number(verification['rtl_interval_max'])} cycles；相对 HLS 周期增加 #{number(verification['cycle_deviation_pct'])}%。"]
    elsif verification.key?("impl_WNS_ns")
      lines += ["", "实现：WNS=#{number(verification['impl_WNS_ns'])} ns；TNS=#{number(verification['impl_TNS_ns'])} ns；timing_met=#{verification['timing_met']}。实际 DSP / BRAM36 / URAM / LUT / FF = #{%w[impl_DSP impl_BRAM36 impl_URAM impl_LUT impl_FF].map { |field| number(verification[field]) }.join(' / ')}。BRAM36 与 HLS 的 BRAM18K 单位不同。"]
    end
    if verification.key?("route_feasible")
      lines += ["", "独立布线门限：route_feasible=#{verification['route_feasible'].nil? ? 'unknown' : verification['route_feasible']}；目标 #{number(verification['impl_target_clock_ns'])} ns；WHS=#{number(verification['impl_WHS_ns'])} ns。历史 HLS 状态不改写。"]
    end
    if record["acceptance_override"]
      override = record.fetch("acceptance_override")
      lines += ["", "后续用户授权：保留原始 #{record['status']}；周期仅检查原上限 #{number(override['max_cycles'])}，依据 #{override['decision_reference']}。"]
    end
    if record["execution_state"]
      lines += ["", "工作流状态：已排队/运行，但没有归档结果行；不作为完成的功能、周期或布线证据。"]
    end
    if !record["has_result_record"]
      lines += ["", "计划中的 estimates 仅为假设，保留在配置和 data.json；此处不展示为实际资源、II 或延迟。"]
    end
    lines += ["", "工具：#{record['tool_version'] ? 'Vitis ' + record['tool_version'] : '未记录 Vitis 版本/不适用'}；源码提交：#{record['source_commit'] ? '`' + record['source_commit'] + '`' : '尚未归档运行源码提交'}。",
              "", "**原始证据：** #{record['evidence'].map { |path| link(path, File.basename(path)) }.join(' · ')}。"]
  end
end
(OUT / "records.md").write(lines.join("\n") + "\n")
puts "Validated #{records.size} IDs, #{records.sum { |record| record['parents'].size }} dependencies; wrote data.json and records.md."
