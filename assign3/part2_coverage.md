# Part 2 documentation coverage

Compared with committed source at d98e8a2c209bc76a77d81be87037b270a12b86e8.

Scope: all 12 currently present root-level Python files. Imported symbols,
inherited unittest/dataclass-generated methods, and local callbacks/test doubles
are not separately defined public interfaces. Private _finite and explicit
__post_init__ hooks are documented as additional coverage.

Tracked-but-deleted helpers were absent and were not restored. Environments,
vendored sources, duplicate submission copies, and bug worktrees are excluded.

## check_cli.py

- <module>: documented
- CliChecks: documented
- CliChecks.invoke: documented
- CliChecks.test_defaults: documented
- CliChecks.test_help: documented
- CliChecks.test_main_passes_parameters_without_opening_gui: documented
- CliChecks.test_main_help_and_invalid_args_do_not_import_rendering: documented
- CliChecks.test_main_dependency_message_and_unexpected_errors: documented
- CliChecks.test_figure_options: documented
- CliChecks.test_headless_figures: documented
- CliChecks.test_invalid_inputs: documented
- CliChecks.test_missing_values: documented

## check_contacts.py

- <module>: documented
- ContactChecks: documented
- ContactChecks.close: documented
- ContactChecks.test_surfaces_and_directions: documented
- ContactChecks.test_no_contact_and_no_ceiling: documented
- ContactChecks.test_both_corners: documented
- ContactChecks.test_restitution_endpoints: documented
- ContactChecks.test_complete_step_order: documented
- ContactChecks.test_default_trajectory: documented

## check_integration.py

- <module>: documented
- IntegrationChecks: documented
- IntegrationChecks.measured: documented
- IntegrationChecks.test_defaults_and_geometry: documented
- IntegrationChecks.test_invalid_state_and_parameters: documented
- IntegrationChecks.test_one_step: documented
- IntegrationChecks.test_zero_gravity: documented
- IntegrationChecks.test_free_fall_and_refinement: documented

## check_scheduling.py

- <module>: documented
- SchedulingChecks: documented
- SchedulingChecks.scheduler: documented
- SchedulingChecks.test_insufficient_and_fractional_time: documented
- SchedulingChecks.test_display_interval_independence: documented
- SchedulingChecks.test_cap_discard_and_remainder: documented
- SchedulingChecks.test_exact_cap_does_not_discard: documented
- SchedulingChecks.test_invalid_elapsed: documented
- SchedulingChecks.test_no_pyvista_import: documented

## cli.py

- <module>: documented
- finite_number: documented
- restitution_value: documented
- timestep_value: documented
- parse_args: documented

## contacts.py

- <module>: documented
- ContactRecord: documented
- ContactRecord.is_impact: documented
- resolve_contacts: documented

## integration.py

- <module>: documented
- step: documented
- complete_step: documented

## main.py

- <module>: documented
- main: documented

## make_figures.py

- <module>: documented
- main: documented

## rendering.py

- <module>: documented
- FixedStepScheduler: documented
- FixedStepScheduler.__post_init__: documented
- FixedStepScheduler.advance: documented
- RenderingDependencyError: documented
- run_simulation: documented

## state.py

- <module>: documented
- _finite: documented
- PhysicsParameters: documented
- PhysicsParameters.__post_init__: documented
- Box: documented
- Box.__post_init__: documented
- Box.validate_for: documented
- CircleState: documented
- CircleState.__post_init__: documented
- CircleState.validate: documented
- CircleState.time: documented

## validation.py

- <module>: documented
- whole_steps: documented
- validate_experiments: documented
- tolerance: documented
- check_close: documented
- check_true: documented
- energy: documented
- sample: documented
- free_fall: documented
- bouncing: documented
- contact_direction: documented
- regression_checks: documented
- write_plots: documented
- run_validation: documented

## Class Attributes review

RenderingDependencyError documents inherited args. The four regression-check
classes document inherited failureException, longMessage and maxDiff.
Their existence/defaults and the five Attributes sections were checked;
the 85-entry presence inventory alone does not establish numpydoc compliance.
Numpydoc lint remains pending.
