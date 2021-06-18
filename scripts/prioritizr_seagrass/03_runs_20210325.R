

# script to run prioritizr scenarios
# the majority of data pre/post processing is done in python
# see prioritizr_scenarios.xlsx for planning table of scenarios


library(prioritizr)
library(tidyverse)



########################################
# read in seagrass and connectivity data
########################################

root <- r'(C:\Users\jcristia\Documents\GIS\MSc_Projects\Impacts)'
gdb <- file.path(root, 'spatial/prioritizr.gdb')
sg_fc <- 'sg_02_pt'
conn_line <- file.path(root, r'(scripts\prioritizr_seagrass\connectivity.csv)')
out_path <- r'(C:\Users\jcristia\Documents\GIS\MSc_Projects\Impacts\scripts\prioritizr_seagrass\outputs)'

# read in feature class
# contains seagrass polygons, costs, connectivity and human impact metrics
sg <- st_read(gdb, layer = sg_fc)

# read in connectivity line dataset
conn <- data.table::fread(conn_line, data.table=FALSE)

# make locked in/out fields logical TRUE/FALSE (fgdb doesn't have a logical data type)
sg$locked_in <- as.logical(sg$locked_in)
sg$locked_out <- as.logical(sg$locked_out)



########################################
# function to evaluate each solution and
# calculate irreplaceability
########################################

evaluate_solution <- function(p1, s1) {
  
  # evaluate the performance of the first solution
  eval_numsel <- eval_n_summary(p1, s1[,'solution_1'])
  eval_cost <- eval_cost_summary(p1, s1[,'solution_1'])
  eval_targets <- eval_target_coverage_summary(p1, s1[,'solution_1'])
  eval_conn <- eval_connectivity_summary(p1, s1[,'solution_1'], data = conn)
  
  # calculate importance (irreplaceability) of the first solution
  rc1 <- p1 %>%
    add_gurobi_solver(gap=0, verbose=FALSE) %>%
    eval_replacement_importance(s1[,'solution_1'])
  rc1 <- tibble::rowid_to_column(rc1, 'id_index') # add id from index for join
  rc1 <- as.data.frame(rc1)
  rc1 <- rc1[c('id_index', 'rc')] # drop shape field
  
  # join solution and importance tables
  s1 <- tibble::rowid_to_column(s1, 'id_index')
  s1_join <- left_join(s1, rc1, by='id_index')
  s1_join <- as_tibble(s1_join)
  s1_join <- select(s1_join, -'Shape')
  
  # output solutions, target evaluation, and summary evaluation to csv
  write.csv(s1_join, 'solution.csv', row.names=FALSE)
  write.csv(eval_targets, 'eval_targets.csv', row.names=FALSE)
  df_summ <- tibble(total_selected=eval_numsel$cost, cost=eval_cost$cost, connectivity=eval_conn$connectivity)
  write.csv(df_summ, 'eval_summary.csv', row.names=FALSE)
  
}



################################################################################
# Solutions
# see prioritizr_scenarios.xlsx for planning table of scenarios
################################################################################



###############################################################
# solution 1:
# select just based on naturalness
# if I apply a penalty of 1 to each impact metric then this 
# will match just adding up the normalized impact metrics
#
# make cost equal for each meadow
# use dummy connectivity feature
###############################################################

out_folder <- 's01_naturalness'
out_dir <- file.path(out_path, out_folder)
dir.create(out_dir)
setwd(out_dir)

features <- c('dummy_con')
targets <- c(0.06)
penalty_value <- 1

p1 <- problem(sg, features, cost_column='cost2') %>%
  add_min_set_objective() %>%
  add_relative_targets(targets) %>%
  add_linear_penalties(penalty = penalty_value, data = 'popn') %>%
  add_linear_penalties(penalty = penalty_value, data = 'ow_perc') %>%
  add_linear_penalties(penalty = penalty_value, data = 'smodperc') %>%
  add_linear_penalties(penalty = penalty_value, data = 'agricult') %>%
  add_linear_penalties(penalty = penalty_value, data = 'cutblock') %>%
  add_linear_penalties(penalty = penalty_value, data = 'gcrab') %>%
  add_linear_penalties(penalty = penalty_value, data = 'reg_sink') %>%
  add_linear_penalties(penalty = penalty_value, data = 'reg_sour') %>%
  add_binary_decisions() %>%
  add_gurobi_solver(gap = 0) %>%
  add_gap_portfolio(number_solutions = 10, pool_gap = 0.1)

s1 <- solve(p1)

evaluate_solution(p1, s1)



##############################################################
# solution 2:
# add connectivity features
# This will give me the top meadows when not considering area
# or meadows already protected. This one will be interesting
# for seeing if any meadows that are already protected would
# have been chosen.

# The conn target needs to be higher than the 0.06 target
# since so much of the connectivity values are concentrated
# in just a few meadows.
# 0.12 is just a guess of where to start (2x 0.06). I will test
# other targets in later solutions.
# I'm still including the dummy_conn because I want the
# solution  to select at least 6% of the meadows.
##############################################################

out_folder <- 's02_addConnFeatures'
out_dir <- file.path(out_path, out_folder)
dir.create(out_dir)
setwd(out_dir)

features <- c('dummy_con', 'dPCpld01','dPCpld60', 'sink_01', 'sink_60', 
              'source01', 'source60', 'gpfill01', 'gpfill60')
targets <- c(0.06, 0.12, 0.12, 0.12, 0.12, 0.12, 0.12, 0.12, 0.12)
penalty_value <- 1

p1 <- problem(sg, features, cost_column='cost2') %>%
  add_min_set_objective() %>%
  add_relative_targets(targets) %>%
  add_linear_penalties(penalty = penalty_value, data = 'popn') %>%
  add_linear_penalties(penalty = penalty_value, data = 'ow_perc') %>%
  add_linear_penalties(penalty = penalty_value, data = 'smodperc') %>%
  add_linear_penalties(penalty = penalty_value, data = 'agricult') %>%
  add_linear_penalties(penalty = penalty_value, data = 'cutblock') %>%
  add_linear_penalties(penalty = penalty_value, data = 'gcrab') %>%
  add_linear_penalties(penalty = penalty_value, data = 'reg_sink') %>%
  add_linear_penalties(penalty = penalty_value, data = 'reg_sour') %>%
  add_binary_decisions() %>%
  add_gurobi_solver(gap = 0) %>%
  add_gap_portfolio(number_solutions = 10, pool_gap = 0.1)

s1 <- solve(p1)

evaluate_solution(p1, s1)



##############################################################
# solution 3:
# lock out already protected areas

# I am locking these out instead of locking them in because
# I want the interpretation to focus on the remaining
# proportion that I need to protect. I'm not concerned with
# an overall percent that I am already protecting.
# I think this is easier to interpret. Also, when I calculate
# importance, I don't want those area included in the list.
##############################################################

out_folder <- 's03_lockout'
out_dir <- file.path(out_path, out_folder)
dir.create(out_dir)
setwd(out_dir)

features <- c('dummy_con', 'dPCpld01','dPCpld60', 'sink_01', 'sink_60', 
              'source01', 'source60', 'gpfill01', 'gpfill60')
targets <- c(0.06, 0.12, 0.12, 0.12, 0.12, 0.12, 0.12, 0.12, 0.12)
penalty_value <- 1

p1 <- problem(sg, features, cost_column='cost2') %>%
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
  add_binary_decisions() %>%
  add_gurobi_solver(gap = 0) %>%
  add_gap_portfolio(number_solutions = 10, pool_gap = 0.1)

s1 <- solve(p1)

evaluate_solution(p1, s1)



##############################################################
# solution 4:
# add area as a target, but keep cost equal

# This will likely change the selection to bigger meadows
# since they still all cost the same (i.e. can meet the target
# with fewer bigger meadows).
##############################################################

out_folder <- 's04_areaTarget'
out_dir <- file.path(out_path, out_folder)
dir.create(out_dir)
setwd(out_dir)

features <- c('area_scaled', 'dPCpld01','dPCpld60', 'sink_01', 'sink_60', 
              'source01', 'source60', 'gpfill01', 'gpfill60')
targets <- c(0.06, 0.12, 0.12, 0.12, 0.12, 0.12, 0.12, 0.12, 0.12)
penalty_value <- 1

p1 <- problem(sg, features, cost_column='cost2') %>%
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
  add_binary_decisions() %>%
  add_gurobi_solver(gap = 0) %>%
  add_gap_portfolio(number_solutions = 10, pool_gap = 0.1)

s1 <- solve(p1)

evaluate_solution(p1, s1)



##############################################################
# solution 5:
# add area as a cost (cost1)

# This will now need to balance selecting high conn, low 
# impacts, and cost of area. 
##############################################################

out_folder <- 's05_areaCost'
out_dir <- file.path(out_path, out_folder)
dir.create(out_dir)
setwd(out_dir)

features <- c('area_scaled', 'dPCpld01','dPCpld60', 'sink_01', 'sink_60', 
              'source01', 'source60', 'gpfill01', 'gpfill60')
targets <- c(0.06, 0.12, 0.12, 0.12, 0.12, 0.12, 0.12, 0.12, 0.12)
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
  add_binary_decisions() %>%
  add_gurobi_solver(gap = 0) %>%
  add_gap_portfolio(number_solutions = 10, pool_gap = 0.1)

s1 <- solve(p1)

evaluate_solution(p1, s1)



##############################################################
# solution 6:
# add connectivity penalty

# This will prioritize selecting meadows that are connected
# in the supplied connectivity matrix.
##############################################################

out_folder <- 's06_connPenalty'
out_dir <- file.path(out_path, out_folder)
dir.create(out_dir)
setwd(out_dir)

features <- c('area_scaled', 'dPCpld01','dPCpld60', 'sink_01', 'sink_60', 
              'source01', 'source60', 'gpfill01', 'gpfill60')
targets <- c(0.06, 0.12, 0.12, 0.12, 0.12, 0.12, 0.12, 0.12, 0.12)
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
  add_gap_portfolio(number_solutions = 10, pool_gap = 0.1)

s1 <- solve(p1)

evaluate_solution(p1, s1)



##############################################################
# solution :

##############################################################



