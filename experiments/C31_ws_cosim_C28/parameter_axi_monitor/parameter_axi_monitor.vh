integer exp_axi_file;
integer exp_axi_transaction = -1;
integer exp_axi_active = 0;
integer exp_axi_load;
integer exp_axi_ar, exp_axi_r, exp_axi_aw, exp_axi_w;
integer exp_axi_ar_valid, exp_axi_r_valid, exp_axi_aw_valid, exp_axi_w_valid;
integer exp_axi_read_bytes;

initial begin
    exp_axi_file = $fopen("reload_parameter_axi.csv", "w");
    if (exp_axi_file == 0) $fatal(1, "Cannot open parameter AXI monitor output");
    $fdisplay(exp_axi_file, "transaction,load_params,ar_requests,r_beats,aw_requests,w_beats,ar_valid_cycles,r_valid_cycles,aw_valid_cycles,w_valid_cycles,read_bytes");
end

always @(posedge ap_clk) begin
    if (!ap_rst_n) begin
        exp_axi_active = 0;
        exp_axi_transaction = -1;
    end else begin
        if ((AESL_start && AESL_ready_p1) || (AESL_start && !AESL_start_p1)) begin
            if (exp_axi_active) $fatal(1, "Overlapping reload-switch transactions");
            exp_axi_transaction = exp_axi_transaction + 1;
            exp_axi_active = 1;
            exp_axi_load = `AUTOTB_DUT_INST.load_params;
            if ((exp_axi_load !== 0) && (exp_axi_load !== 1))
                $fatal(1, "Unknown load_params control value");
            exp_axi_ar = 0;
            exp_axi_r = 0;
            exp_axi_aw = 0;
            exp_axi_w = 0;
            exp_axi_ar_valid = 0;
            exp_axi_r_valid = 0;
            exp_axi_aw_valid = 0;
            exp_axi_w_valid = 0;
            exp_axi_read_bytes = 0;
        end
        if (exp_axi_active) begin
            if (parameters_ARVALID) exp_axi_ar_valid = exp_axi_ar_valid + 1;
            if (parameters_RVALID) exp_axi_r_valid = exp_axi_r_valid + 1;
            if (parameters_AWVALID) exp_axi_aw_valid = exp_axi_aw_valid + 1;
            if (parameters_WVALID) exp_axi_w_valid = exp_axi_w_valid + 1;
            if (parameters_ARVALID && parameters_ARREADY) begin
                exp_axi_ar = exp_axi_ar + 1;
                exp_axi_read_bytes = exp_axi_read_bytes + ((parameters_ARLEN + 1) << parameters_ARSIZE);
            end
            if (parameters_RVALID && parameters_RREADY) exp_axi_r = exp_axi_r + 1;
            if (parameters_AWVALID && parameters_AWREADY) exp_axi_aw = exp_axi_aw + 1;
            if (parameters_WVALID && parameters_WREADY) exp_axi_w = exp_axi_w + 1;
        end else if (parameters_ARVALID || parameters_RVALID || parameters_AWVALID || parameters_WVALID) begin
            $fatal(1, "Parameter AXI traffic outside a measured transaction");
        end
        if (AESL_done && exp_axi_active) begin
            $fdisplay(exp_axi_file, "%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d",
                      exp_axi_transaction, exp_axi_load, exp_axi_ar, exp_axi_r, exp_axi_aw, exp_axi_w,
                      exp_axi_ar_valid, exp_axi_r_valid, exp_axi_aw_valid, exp_axi_w_valid, exp_axi_read_bytes);
            $fflush(exp_axi_file);
            $display("EXP_PARAMETER_AXI transaction=%0d load=%0d reads=%0d beats=%0d bytes=%0d",
                     exp_axi_transaction, exp_axi_load, exp_axi_ar, exp_axi_r, exp_axi_read_bytes);
            exp_axi_active = 0;
            if (exp_axi_transaction == AUTOTB_TRANSACTION_NUM - 1) $fclose(exp_axi_file);
        end
    end
end
