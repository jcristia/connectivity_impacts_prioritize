# the majority of data pre/post processing is done in python
# this is me fumbling through R


library(prioritizr)
library(sf)
library(sp)
library(tidyverse)
options(tibble.width = Inf)

root = r'(C:\Users\jcristia\Documents\GIS\MSc_Projects\Impacts)'
gdb = file.path(root, 'spatial/prioritizr.gdb')
sg_fc <- 'sg_02_pt'
conn_line <- file.path(root, r'(scripts\prioritizr_seagrass\connectivity.csv)')
out_path <- r'(C:\Users\jcristia\Documents\GIS\MSc_Projects\Impacts\scripts\prioritizr_seagrass\outputs)'

sg <- st_read(gdb, layer = sg_fc) # the sf library lets me read in fgdb format
#sg <- as(sg, "Spatial") # if you want to convert it from sf to sp (spatialdataframe)

conn <- data.table::fread(conn_line, data.table=FALSE)

# make locked in/out fields logical TRUE/FALSE (Arc doesn't have a logical data type)
sg$locked_in <- as.logical(sg$locked_in)
sg$locked_out <- as.logical(sg$locked_out)

########################################################
# test 1: with everything
########################################################

out_folder <- 's1_test'
out_dir <- file.path(out_path, out_folder)
dir.create(out_dir)
setwd(out_dir)

features <- c('area_scaled', 'dPCpld01','dPCpld60', 'sink_01', 'sink_60', 'source01', 
             'source60', 'gpfill01', 'gpfill60')
targets <- c(0.16, 0.16, 0.16, 0.16, 0.16, 0.16, 0.16, 0.16, 0.16)
penalty_value <- 1

p1 <- problem(sg, features, cost_column='cost1') %>%
      add_min_set_objective() %>%
      add_relative_targets(targets) %>%
      add_locked_out_constraints('locked_out') %>%
      add_linear_penalties(penalty = penalty_value, data = 'popn') %>%
      add_linear_penalties(penalty = penalty_value, data = 'ow_perc') %>%
      add_linear_penalties(penalty = penalty_value, data = 'smodperc') %>%
      add_linear_penalties(penalty = penalty_value, data = 'agricult') %>%
      add_linear_penalties(penalty = penalty_value, data = 'cutblock') %>%
      add_linear_penalties(penalty = penalty_value, data = 'gcrab') %>%
      add_linear_penalties(penalty = penalty_value, data = 'reg_sink') %>%
      add_linear_penalties(penalty = penalty_value, data = 'reg_sour') %>%
      add_connectivity_penalties(penalty = 1, data = conn) %>%
      add_binary_decisions() %>%
      add_gurobi_solver(gap = 0) %>%
      add_gap_portfolio(number_solutions = 2, pool_gap = 0.1)

# Connectivity penalty has to be kept low or else you get a large/small value error
# "...a common issue is when a relatively large penalty value is specified for 
# boundary (add_boundary_penalties()) or connectivity penalties 
# (add_connectivity_penalties()). This can be fixed by trying a smaller penalty 
# value. In such cases, the original penalty value supplied was so high that the
# optimal solution would just have selected every single planning unit in the 
# solution---and this may not be especially helpful anyway."
# WELL ACTUALLY, the issue was the area(cost) values where too high. I converted
# these to km2.

# btw, you can force run gurboi:
#s3 <- p3 %>%
#  add_gurobi_solver(numeric_focus = TRUE) %>%
#  solve(force = TRUE)

print(p1)
presolve_check(p1)
s1 <- solve(p1)

# evaluate the performance of the solution
print(s1)
eval_numsel <- eval_n_summary(p1, s1[,'solution_1'])
eval_cost <- eval_cost_summary(p1, s1[,'solution_1'])
eval_targets <- eval_target_coverage_summary(p1, s1[,'solution_1'])
eval_conn <- eval_connectivity_summary(p1, s1[,'solution_1'], data = conn)
# I wonder if the conn amount is just based on summing up all the probabilities.

# Importance (irreplaceability)
rc1 <- p1 %>%
       add_gurobi_solver(gap=0, verbose=FALSE) %>%
       eval_replacement_importance(s1[,'solution_1'])
rc1 <- tibble::rowid_to_column(rc1, 'id_index') # add id from index for join
rc1 <- as.data.frame(rc1)
rc1 <- rc1[c('id_index', 'rc')] # drop shape field

# join solution
s1 <- tibble::rowid_to_column(s1, 'id_index')
s1_join <- left_join(s1, rc1, by='id_index')
s1_join <- as_tibble(s1_join)
s1_join <- select(s1_join, -'Shape')

# output to csv
write.csv(s1_join, 'solution.csv', row.names=FALSE)
# output performance evaluation
write.csv(eval_targets, 'eval_targets.csv', row.names=FALSE)
df_summ <- tibble(total_selected=eval_numsel$cost, cost=eval_cost$cost, connectivity=eval_conn$connectivity)
write.csv(df_summ, 'eval_summary.csv', row.names=FALSE)

# calc importance for all solutions
# This takes a long time to calculate, and I'm not sure if I even need to
# get an average of importance right now. For now, I'll just use the top solution.
# solution_columns <- which(grepl("solution", names(s1)))
# j <- 1
# for (i in solution_columns){
#   rc <- p1 %>%
#     add_gurobi_solver(gap=0, verbose=FALSE) %>%
#     eval_replacement_importance(s1[i])
#   rc <- tibble::rowid_to_column(rc, 'id') # add id from index for join
#   rc <- as.data.frame(rc)
#   rc <- rc[c('id', 'rc')]
#   names(rc)[names(rc)=='rc'] <- paste('rc_', toString(j), sep='')
#   if (j > 1){
#     rcs_all <- left_join(rcs_all, rc, by='id')
#   }
#   else{
#     rcs_all <- rc
#   }
#   j <- j + 1
# }


########################################################
# test 2: no connectivity penalty
########################################################

out_folder <- 's2_test'
out_dir <- file.path(out_path, out_folder)
dir.create(out_dir)
setwd(out_dir)

features <- c('area_scaled', 'dPCpld01','dPCpld60', 'sink_01', 'sink_60', 'source01', 
              'source60', 'gpfill01', 'gpfill60')
targets <- c(0.16, 0.16, 0.16, 0.16, 0.16, 0.16, 0.16, 0.16, 0.16)
penalty_value <- 1

p1 <- problem(sg, features, cost_column='cost1') %>%
  add_min_set_objective() %>%
  add_relative_targets(targets) %>%
  add_locked_out_constraints('locked_out') %>%
  add_linear_penalties(penalty = penalty_value, data = 'popn') %>%
  add_linear_penalties(penalty = penalty_value, data = 'ow_perc') %>%
  add_linear_penalties(penalty = penalty_value, data = 'smodperc') %>%
  add_linear_penalties(penalty = penalty_value, data = 'agricult') %>%
  add_linear_penalties(penalty = penalty_value, data = 'cutblock') %>%
  add_linear_penalties(penalty = penalty_value, data = 'gcrab') %>%
  add_linear_penalties(penalty = penalty_value, data = 'reg_sink') %>%
  add_linear_penalties(penalty = penalty_value, data = 'reg_sour') %>%
  #add_connectivity_penalties(penalty = 1, data = conn) %>%
  add_binary_decisions() %>%
  add_gurobi_solver(gap = 0) %>%
  add_gap_portfolio(number_solutions = 2, pool_gap = 0.1)

s1 <- solve(p1)

# evaluate the performance of the solution
eval_numsel <- eval_n_summary(p1, s1[,'solution_1'])
eval_cost <- eval_cost_summary(p1, s1[,'solution_1'])
eval_targets <- eval_target_coverage_summary(p1, s1[,'solution_1'])
eval_conn <- eval_connectivity_summary(p1, s1[,'solution_1'], data = conn)

# Importance (irreplaceability)
rc1 <- p1 %>%
  add_gurobi_solver(gap=0, verbose=FALSE) %>%
  eval_replacement_importance(s1[,'solution_1'])
rc1 <- tibble::rowid_to_column(rc1, 'id_index')
rc1 <- as.data.frame(rc1)
rc1 <- rc1[c('id_index', 'rc')]

# join solution
s1 <- tibble::rowid_to_column(s1, 'id_index')
s1_join <- left_join(s1, rc1, by='id_index')
s1_join <- as_tibble(s1_join)
s1_join <- select(s1_join, -'Shape')

# output to csv
write.csv(s1_join, 'solution.csv', row.names=FALSE)
write.csv(eval_targets, 'eval_targets.csv', row.names=FALSE)
df_summ <- tibble(total_selected=eval_numsel$cost, cost=eval_cost$cost, connectivity=eval_conn$connectivity)
write.csv(df_summ, 'eval_summary.csv', row.names=FALSE)


########################################################
########################################################



