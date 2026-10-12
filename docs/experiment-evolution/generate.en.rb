# frozen_string_literal: true

require "json"
require "pathname"

OUT = Pathname.new(__dir__)
ROOT = OUT.parent.parent
BASE = JSON.parse((OUT / "data.json").read)
TRANSLATION = JSON.parse((OUT / "catalog.en.json").read)
STATUS = {
  "infeasible" => "Resource/performance gate not met", "analysis_complete" => "Analysis complete",
  "fail" => "Run failed", "invalid_config" => "Invalid configuration", "timeout" => "Timed out",
  "csim_pass" => "C simulation passed", "provisional" => "Candidate; final acceptance pending",
  "impl_complete" => "Implementation complete; check timing separately", "pass" => "Local experiment passed",
  "cosim_complete" => "RTL co-simulation complete", "planned" => "Prepared; no archived measurements"
}.freeze
FLAGS = {
  "未归档测量" => "No archived measurements", "II 未达目标" => "II target missed",
  "HLS 时序警告" => "HLS timing warning", "配置无效" => "Invalid configuration",
  "主机 OOM" => "Host OOM", "实现时序未达标" => "Routed timing failed",
  "仅诊断，沿用父设计 HLS 门槛" => "Diagnostic only; parent HLS gates retained"
}.freeze

def number(value, decimals = 4)
  return "unknown" if value.nil?
  return value.to_i.to_s if value == value.to_i

  format("%.#{decimals}f", value).sub(/0+\z/, "").sub(/\.\z/, "")
end

def link(path, label = nil)
  target = (ROOT / path).relative_path_from(OUT).to_s
  "[#{label || path}](#{target})"
end

abort "Translation snapshot differs" unless BASE.fetch("source_commit") == TRANSLATION.fetch("source_commit")
abort "Translation sections differ" unless BASE.fetch("sections").map { |section| section["key"] } == TRANSLATION.fetch("sections").map { |section| section["key"] }
translations = TRANSLATION.fetch("sections").flat_map { |section| section.fetch("records") }
ids = translations.map(&:first)
abort "Translation IDs differ or are duplicated" unless ids == BASE.fetch("records").map { |record| record["id"] } && ids.uniq.size == ids.size
translations.each do |row|
  abort "Incomplete translation: #{row[0]}" unless row.size == 4 && row.all? { |value| value.is_a?(String) && !value.empty? }
end
by_id = translations.to_h { |row| [row[0], row] }
sections = BASE.fetch("sections").zip(TRANSLATION.fetch("sections")).map do |original, translated|
  original.merge(translated.slice("title", "question"))
end
records = BASE.fetch("records").map do |original|
  id, title, change, issue = by_id.fetch(original.fetch("id"))
  flags = original.fetch("flags").map do |flag|
    if flag.start_with?("超预算: ")
      "Over budget: #{flag.delete_prefix('超预算: ')}"
    else
      FLAGS.fetch(flag)
    end
  end
  hls = original["hls"]
  verification = original.fetch("verification")
  quality = original["quality"]
  if quality && quality.dig("provenance", "method") == "本次仿真；逐图范围见原始验证记录"
    quality = quality.merge("provenance" => quality.fetch("provenance").merge("method" => "Current simulation; image coverage is recorded in the original validation archive"))
  end
  result = if original["run_kind"] == "cosim"
             "RTL #{verification['rtl_status'] || 'incomplete'} / #{number(verification['rtl_latency_max'])} cycles"
           elsif original["run_kind"] == "impl"
             if verification.key?("impl_WNS_ns")
               "Routed WNS #{number(verification['impl_WNS_ns'])} ns"
             elsif flags.include?("Host OOM")
               "Host OOM; no routed results"
             else
               "Physical implementation incomplete"
             end
           elsif hls && original["scope"] == "frame"
             "HLS estimate #{number(hls['latency_ms_est'])} ms / DSP #{number(hls['DSP'])}"
           elsif hls
             "#{original['scope'] == 'layer' ? 'Layer' : 'PE'}: DSP #{number(hls['DSP'])} / LUT #{number(hls['LUT'])}"
           elsif quality
             "C simulation / avg delta PSNR #{number(quality['delta_vs_float_db'])} dB"
           else
             STATUS.fetch(original.fetch("status"))
           end
  original.merge("title" => title, "change" => change, "issue" => issue,
                 "flags" => flags, "quality" => quality,
                 "graph" => original.fetch("graph").merge("result" => result, "flags" => flags.empty? ? STATUS.fetch(original["status"]) : flags.join("; ")))
end
data = BASE.merge("sections" => sections, "records" => records, "edge_kinds" => TRANSLATION.fetch("edge_kinds"))
(OUT / "data.en.json").write(JSON.pretty_generate(data) + "\n")

lines = ["# All Experiments: Dependencies, Changes, Effects, and Issues", "",
         "[中文版](records.md)", "",
         "Snapshot: `#{data['source_commit']}`; #{records.size} experiments, #{data['counts']['with_result_record']} result archives, and #{data['counts']['plan_only']} plans/preparation records.", "",
         "Result records include failures, timeouts, and invalid configurations. Edges represent design, parameter, integration, and acceptance dependencies, not sequential Git clone history.", "",
         "HLS time uses cycles * max(target period, HLS estimated period) / 10^6 ms. This neither establishes timing closure after uncertainty nor measures board performance. Budgets: DSP <= 1248, BRAM18K <= 288, URAM <= 64, LUT <= 81984, FF <= 163968. LUT/FF budgets are 70% of device capacity.", "",
         "Ordinary synthesis rows may inherit quality from an independent precision reference; provenance is shown below. Actual per-run image coverage is recorded by image_count in the original configuration. Implementation/RTL rows preserve inherited HLS fields only in data.en.json's registry_raw; displayed results come from that verification step.", "",
         "[Guide](../0004-experiment-evolution.en.md) | [Overview](overview.en.svg) | [Machine-readable data](data.en.json)", "",
         "## Route Index", "", "| Route | IDs | Diagram |", "| --- | --- | --- |"]
by_section = records.group_by { |record| record["section"] }
sections.each do |section|
  links = by_section.fetch(section["key"]).map { |record| "[#{record['id']}](##{record['id'].downcase})" }.join(" ")
  lines << "| [#{section['title']}](##{section['key']}) | #{links} | [Graph](#{section['key']}.en.svg) |"
end
sections.each do |section|
  lines += ["", "<a id=\"#{section['key']}\"></a>", "", "## #{section['title']}", "",
            section.fetch("question"), "", "[Evolution graph](#{section['key']}.en.svg). Route evidence: #{section['evidence'].map { |path| link(path) }.join(' | ')}."]
  by_section.fetch(section["key"]).each do |record|
    lines += ["", "<a id=\"#{record['id'].downcase}\"></a>", "", "### #{record['id']}: #{record['title']}", ""]
    parents = record["parents"].map { |parent| "[#{parent['id']}](##{parent['id'].downcase}) (#{data['edge_kinds'].fetch(parent['kind'])})" }
    lines << "**Based on:** #{parents.empty? ? 'Original src/ baseline; no preceding experiment.' : parents.join('; ') + '.'}"
    lines += ["", "**Change:** #{record['change']}", "", "**Effects and issues:** #{record['issue']}", "",
              "**Status:** `#{record['status']}` / #{STATUS.fetch(record['status'])}; scope `#{record['scope']}`; step `#{record['run_kind']}`."]
    lines << "Additional checks: #{record['flags'].join('; ')}." unless record["flags"].empty?
    hls = record["hls"]
    if hls
      lines += ["", "| HLS measurement/estimate | Value |", "| --- | --- |",
                "| Target / estimated period | #{number(hls['clock_target_ns'])} / #{number(hls['clock_est_ns'])} ns |",
                "| Latency / interval | #{number(hls['latency_cycles'])} / #{number(hls['interval_cycles'])} cycles |",
                "| Registry time conversion | #{number(hls['latency_ms_est'], 8)} ms (#{record['scope']} scope; converted at #{number(hls['time_basis_ns'])} ns) |",
                "| DSP / BRAM18K / URAM | #{number(hls['DSP'])} / #{number(hls['BRAM18K'])} / #{number(hls['URAM'])} |",
                "| LUT / FF | #{number(hls['LUT'])} / #{number(hls['FF'])} |",
                "| Checked II targets | #{hls['ii_ok'].nil? ? 'Not recorded' : hls['ii_ok'] ? 'Met' : 'Missed'} |"]
    end
    warnings = record["hls_timing_warnings"]
    unless warnings.empty?
      worst = warnings.max_by { |warning| warning["estimated_ns"] || 0 }
      lines += ["", "HLS 200-871: logic budget #{number(worst['target_ns'])} - #{number(worst['uncertainty_ns'])} = #{number(worst['effective_budget_ns'])} ns; maximum warned path estimate #{number(worst['estimated_ns'])} ns. See the original synthesis log."]
    end
    functional = record["functional"]
    if functional && functional["csim_pass"]
      values = ["C simulation passed", "bit_exact=#{functional['bit_exact'].nil? ? 'not recorded' : functional['bit_exact']}"]
      values << "butterfly MSE=#{functional['butterfly_mse']}" if functional["butterfly_mse"]
      values << "six-pixel border MSE=#{functional['border_mse']}" if functional["border_mse"]
      lines += ["", "Function: #{values.join('; ')}. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output."]
    end
    quality = record["quality"]
    if quality
      provenance = quality.fetch("provenance")
      origin = provenance["path"] ? link(provenance["path"]) : "current simulation (#{provenance['image_count'] || 'count not separately recorded'} images; see original archive)"
      lines += ["", "Quality: average PSNR against GT = #{number(quality['psnr_gt_db'], 6)} dB; average delta PSNR against float = #{number(quality['delta_vs_float_db'], 6)} dB. Source: #{origin}."]
    end
    verification = record["verification"]
    if record["inherited_hls_parent"]
      lines += ["", "Inherited HLS estimates come from [#{record['inherited_hls_parent']}](##{record['inherited_hls_parent'].downcase}); they are not new measurements from this step."]
    end
    if verification.key?("rtl_status")
      lines += ["", "RTL: #{verification['rtl_status']}; maximum latency #{number(verification['rtl_latency_max'])} cycles; maximum interval #{number(verification['rtl_interval_max'])} cycles; #{number(verification['cycle_deviation_pct'])}% more cycles than HLS."]
    elsif verification.key?("impl_WNS_ns")
      lines += ["", "Implementation: WNS=#{number(verification['impl_WNS_ns'])} ns; TNS=#{number(verification['impl_TNS_ns'])} ns; timing_met=#{verification['timing_met']}. Actual DSP / BRAM36 / URAM / LUT / FF = #{%w[impl_DSP impl_BRAM36 impl_URAM impl_LUT impl_FF].map { |field| number(verification[field]) }.join(' / ')}. BRAM36 and HLS BRAM18K are different units."]
    end
    unless record["has_result_record"]
      lines += ["", "Planned estimates remain hypotheses in the configuration/data.en.json. They are not displayed as measured resources, II, or latency."]
    end
    lines += ["", "Tool: #{record['tool_version'] ? 'Vitis ' + record['tool_version'] : 'Vitis version not recorded/not applicable'}; source commit: #{record['source_commit'] ? '`' + record['source_commit'] + '`' : 'run source commit not yet archived'}.",
              "", "**Original evidence:** #{record['evidence'].map { |path| link(path, File.basename(path)) }.join(' | ')}."]
  end
end
(OUT / "records.en.md").write(lines.join("\n") + "\n")
puts "Translated #{records.size} IDs; reused #{records.sum { |record| record['parents'].size }} dependencies and all measured results."
