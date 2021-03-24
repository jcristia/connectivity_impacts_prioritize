# the majority of data formatting is done in python


library(prioritizr)
library(sf)
library(sp)
library(tidyverse)
options(tibble.width = Inf)

root = r'(C:\Users\jcristia\Documents\GIS\MSc_Projects\Impacts)'
gdb = file.path(root, 'spatial/prioritizr.gdb')
sg_fc <- 'sg_02_pt'
sg <- st_read(gdb, layer = sg_fc) # the sf library lets me read in fgdb format
#sg <- as(sg, "Spatial") # if you want to convert it from sf to sp (spatialdataframe)

# make locked in/out fields logical TRUE/FALSE (Arc doesn't have this data type)
sg$locked_in <- as.logical(sg$locked_in)
sg$locked_out <- as.logical(sg$locked_out)

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
      add_binary_decisions() %>%
      add_gurobi_solver(gap = 0) %>%
      add_gap_portfolio(number_solutions = 5, pool_gap = 0.1)
      
print(p1)
presolve_check(p1)
s1 <- solve(p1)

# evaluate the performance of the solution
print(s1)
eval_n_summary(p1, s1[,'solution_1'])
eval_cost_summary(p1, s1[,'solution_1'])
eval_target_coverage_summary(p1, s1[,'solution_1'])
#eval_connectivity_summary(p1, s1[,'solution_1'], data = '')

# Importance (irreplaceability)
rc1 <- p1 %>%
       add_gurobi_solver(gap=0) %>%
       eval_replacement_importance(s1[,'solution_1'])


# calc importance for all solutions
solution_columns <- which(grepl("solution", names(s1)))
j <- 1
for (i in solution_columns){
  rc <- p1 %>%
    add_gurobi_solver(gap=0, verbose=FALSE) %>%
    eval_replacement_importance(s1[i])
  rc <- tibble::rowid_to_column(rc, 'id') # add id from index for join
  rc <- as.data.frame(rc)
  rc <- rc[c('id', 'rc')]
  if (j > 1){
    rcs_all <- left_join(rcs_all, rc, by='id')
  }
  else{
    rcs_all <- rc
  }
  j <- j + 1
}


# TODO:
# add connectivity penalty once I have matrix
# output solutions and irreplaceability to csv (add id to s1, join, drop fields)
# for selection frequency plots, BCMCA did 100 runs.





