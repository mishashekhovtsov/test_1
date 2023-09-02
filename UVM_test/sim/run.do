set need_del 0
set debug 1
set classdebug 1
set den_gen 0
if {[file exist work/_info]} {
  echo "Work library found"
} else {
  vlib work
  vmap work work
}

if {$debug} {
      set opt -O4
      set sopt -voptargs="+acc=rn"
} else {
      set opt -O4
      set sopt -vopt
} 

if {$classdebug} {
      set cld -classdebug
} else {
      set cld -noclassdebug
} 


if {$need_del} {
   vdel -all work
   vlib work
}

set modelsim_dir /home/mixa/Programs/questasim
set uvm_lib_path /home/mixa/Programs/questasim/uvm-1.2
set uvm_src_path /home/mixa/Programs/questasim/verilog_src/uvm-1.2/src

vlog $opt +incdir+../tb ../tb/testbenches/test_1_tb_pkg.svh -sv 
vlog $opt +incdir+../tb ../tb/testbenches/test_1_tb.sv -sv 
vlog $opt +incdir+../tb ../src/rtl.sv
vlog $opt +incdir+../tb ../tb/uvm_classes/my_sequence.svh -sv 
vlog $opt +incdir+../tb ../tb/uvm_classes/my_driver.svh -sv 


vsim  $sopt  +UVM_VERBOSITY=UVM_HIGH  $cld \
        -uvmcontrol=all work.top  +UVM_TESTNAME=my_test

if {$classdebug} {
      run 500 ns
} 


view -undock wave 
#do proj_wave.do 


