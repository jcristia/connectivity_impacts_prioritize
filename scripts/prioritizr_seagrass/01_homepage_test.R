# testing code that is on the home page of prioritizr.net

library(prioritizr)

# load planning unit data
data(sim_pu_polygons)
# show the first 6 rows in the attribute table
head(sim_pu_polygons@data)
# plot the planning units and color them according to acquisition cost
spplot(sim_pu_polygons, "cost", main = "Planning unit cost",
       xlim = c(-0.1, 1.1), ylim = c(-0.1, 1.1))
# plot the planning units and show which planning units are inside protected
# areas (colored in yellow)
spplot(sim_pu_polygons, "locked_in", main = "Planning units in protected areas",
       xlim = c(-0.1, 1.1), ylim = c(-0.1, 1.1))

# load feature data
data(sim_features)
# plot the distribution of suitable habitat for each feature
plot(sim_features, main = paste("Feature", seq_len(nlayers(sim_features))),
     nr = 2)

# create problem
p1 <- problem(sim_pu_polygons, features = sim_features,
              cost_column = "cost") %>%
  add_min_set_objective() %>%
  add_relative_targets(0.15) %>%
  add_binary_decisions() %>%
  add_default_solver(gap = 0)

# solve the problem
s1 <- solve(p1)

# extract the objective
print(attr(s1, "objective"))

# extract time spent solving the problem
print(attr(s1, "runtime"))

# extract state message from the solver
print(attr(s1, "status"))

# plot the solution
spplot(s1, "solution_1", main = "Solution", at = c(0, 0.5, 1.1),
       col.regions = c("grey90", "darkgreen"), xlim = c(-0.1, 1.1),
       ylim = c(-0.1, 1.1))

# calculate solution cost
print(eval_cost_summary(p1, s1[, "solution_1"]), width = Inf)

# calculate information describing how well the targets are met by the solution
print(eval_target_coverage_summary(p1, s1[, "solution_1"]), width = Inf)




# create new problem with locked in constraints added to it
p2 <- p1 %>%
  add_locked_in_constraints("locked_in")
# solve the problem
s2 <- solve(p2)
# plot the solution
spplot(s2, "solution_1", main = "Solution", at = c(0, 0.5, 1.1),
       col.regions = c("grey90", "darkgreen"), xlim = c(-0.1, 1.1),
       ylim = c(-0.1, 1.1))


# create new problem with boundary penalties added to it
p3 <- p2 %>%
  add_boundary_penalties(penalty = 300, edge_factor = 0.5)
# solve the problem
s3 <- solve(p3)
# plot the solution
spplot(s3, "solution_1", main = "Solution", at = c(0, 0.5, 1.1),
       col.regions = c("grey90", "darkgreen"), xlim = c(-0.1, 1.1),
       ylim = c(-0.1, 1.1))


# create new problem with contiguity constraints
p4 <- p3 %>%
  add_contiguity_constraints()
# solve the problem
s4 <- solve(p4)
# plot the solution
spplot(s4, "solution_1", main = "Solution", at = c(0, 0.5, 1.1),
       col.regions = c("grey90", "darkgreen"), xlim = c(-0.1, 1.1),
       ylim = c(-0.1, 1.1))


# solve the problem
rc <- p4 %>%
  add_default_solver(gap = 0, verbose = FALSE) %>%
  eval_replacement_importance(s4[, "solution_1"])

# set infinite values as 1.09 so we can plot them
rc$rc[rc$rc > 100] <- 1.09

# plot the importance scores
# planning units that are truly irreplaceable are shown in red
spplot(rc, "rc", main = "Irreplaceability", xlim = c(-0.1, 1.1),
       ylim = c(-0.1, 1.1), at = c(seq(0, 0.9, 0.1), 1.01, 1.1),
       col.regions = c("#440154", "#482878", "#3E4A89", "#31688E", "#26828E",
                       "#1F9E89", "#35B779", "#6DCD59", "#B4DE2C", "#FDE725",
                       "#FF0000"))


# my notes:
# if you look at the % and costs of this solution you can see that they are a lot
# higher now that we have constraints to deal with
print(eval_target_coverage_summary(p4, s4[, "solution_1"]), width = Inf)
print(eval_cost_summary(p4, s4[, "solution_1"]), width = Inf)



