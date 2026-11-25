#!/usr/bin/env python3
"""sim-first-check: deterministic gate for the SIMULATE-FIRST INTERVENTION surface
(the company order: simulate everything first, then intervene on the simulation).
Stdlib only, offline, free.
Owns the ORDER + COUNTERFACTUAL layer. Not synthetic-user data sufficiency
(synthetic-user-check SU-0..SU-6), not notification decision ownership
(notif-model-check NM-0..NM-5), not eval design (eval-design-check).
Sources (read 2026-11-22):
- Springer, Discover Artificial Intelligence, "A generative agent system-based
  model for group behavior prediction and dynamic intervention"
  https://link.springer.com/article/10.1007/s44163-026-01484-w (read in full):
  the task is two coupled sub-problems -- crowd evolution PREDICTION forms the
  foundation, and only on it does intervention policy design stand; the
  counterfactual intervention module embeds a causal graph in the decision loop
  and performs counterfactual rollouts to identify critical intervention
  variables; intervention strategies built on statistical association (rule-based
  trial-and-error, black-box RL) fail out-of-distribution and induce unintended
  side effects; observational datasets contain little counterfactual information,
  so fit metrics (MSE / accuracy on history) are insufficient -- evaluation must
  also cover OOD robustness and the true utility of the intervention strategy;
  scale is made feasible by a hierarchical mixed-agent architecture (a large
  model for complex reasoning, a distilled small model for high-frequency
  interactions).
- The Decision Lab, "Behavioral Research Methods" (read 2026-11-22)
  https://thedecisionlab.com/guides/from-surveys-to-simulations-behavioral-research-methods
  -- simulated populations narrow options and stress-test designs before a live
  launch (their digital-wellness case: decision logic tested against synthetic
  members in a validation harness, design failures surfaced in an afternoon);
  when a decision carries real risk, the strongest options are still confirmed
  with real people -- simulation narrows, it does not replace live validation.
- House definition (founder, 2026-11-22, primary): "We are the Simulation
  Company -- simulating everything, and then intervention": society / population
  / behavior simulation first (Manager prediction, synthetic users, digital
  twins, generative agents), intervention second (notifications, words, every
  product surface). Behaviour data is the moat and the company sells the upper
  layer only; the known logging gap (which word was chosen, with what
  probability) keeps ManagerBench real cases at zero.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    o=d.get("order") or {}
    if not o.get("simulate_first_order_recorded"): f.append("SI-0 the simulate-first order is not recorded (which surfaces must be simulated before they may intervene is nowhere written; an unrecorded order defaults to intervening on instinct)")
    if not o.get("every_intervention_surface_has_named_simulation"): f.append("SI-0 not every intervention surface has a named simulation (a surface with no simulation behind it -- notifications, paywall, home words, distribution copy -- intervenes blind by construction)")
    if not o.get("no_intervention_ships_without_prior_simulation_run"): f.append("SI-0 interventions can ship without a prior simulation run (the prediction task is the foundation: no rollout record, no live intervention -- exceptions are how the order dies)")
    if not o.get("simulation_run_logged_with_date_and_inputs"): f.append("SI-0 simulation runs are not logged with date and inputs (an unlogged run cannot be audited, replayed, or compared with the outcome it claimed to predict)")
    p=d.get("population") or {}
    if not p.get("population_built_from_real_behavior_data"): f.append("SI-1 the simulated population is not built from real behavior data (agents invented from demographics alone are a horoscope: the population must be grounded in measured behavior -- onboarding answers, reaction history, the founder twin as the depth case)")
    if not p.get("heterogeneity_preserved_not_average_user"): f.append("SI-1 the population collapses to one average user (group behavior emerges from heterogeneous agents; an average-user simulation predicts a person who does not exist)")
    if not p.get("fidelity_validated_against_real_responses"): f.append("SI-1 simulation fidelity is never validated against real responses (fit to history is not enough: predictions must be scored against what real people then did, or the simulation grades itself)")
    if not p.get("person_and_population_layers_both_present"): f.append("SI-1 only one layer is simulated (the company definition runs person-level twins AND population/society simulation; a per-person predictor with no population layer misses emergence, and a population with no person layer cannot personalize an intervention)")
    c=d.get("counterfactual") or {}
    if not c.get("candidates_compared_in_simulation_before_live"): f.append("SI-2 candidate interventions are not compared in simulation before going live (choosing live is running the experiment on real users first -- the sandbox exists so the comparison happens on simulated members first)")
    if not c.get("do_nothing_baseline_included"): f.append("SI-2 rollouts omit the do-nothing baseline (an intervention that cannot beat simulated no-intervention has no predicted effect, only a hope)")
    if not c.get("critical_variables_identified_from_rollouts"): f.append("SI-2 rollouts do not identify the critical intervention variables (the point of counterfactual rollouts is learning WHICH lever moves the outcome -- a ranking without named variables cannot be reused)")
    if not c.get("side_effects_and_ood_checked"): f.append("SI-2 side effects and out-of-distribution behaviour are not checked (association-based policies fail OOD and induce unintended side effects; the simulation must probe where the intervention breaks, not only where it works)")
    s=d.get("selection") or {}
    if not s.get("live_choice_taken_from_simulation_ranking"): f.append("SI-3 the live intervention is not taken from the simulation ranking (if the shipped choice is not the simulation's choice, the simulation is decoration and the real decider is unnamed)")
    if not s.get("chosen_intervention_carries_its_prediction"): f.append("SI-3 the chosen intervention does not carry its simulated prediction with it (word + probability + predicted response must travel with the send, or the outcome can never be scored against the prediction -- this is the logging gap that keeps ManagerBench at zero real cases)")
    if not s.get("fallback_is_prior_serving_not_guess"): f.append("SI-3 there is no recorded fallback when simulation is unavailable (the prior serves meanwhile; silently shipping an unsimulated guess hides a simulation outage as a quality drop)")
    a=d.get("architecture") or {}
    if not a.get("hierarchical_models_large_reasoning_small_high_frequency"): f.append("SI-4 one model tier does everything (scale needs the hierarchy: a large model for complex reasoning, a cheap distilled model for high-frequency simulated interactions -- full-scale reasoning on every agent interaction does not survive population scale)")
    if not a.get("rollout_cost_measured_free_or_prepaid_only"): f.append("SI-4 rollout cost is not measured (simulation volume is a cost line: cost per rollout must be known, and runs stay on free tiers or already-paid credit -- no new API payment to simulate harder)")
    if not a.get("simulation_speed_fits_decision_cadence"): f.append("SI-4 simulation is too slow for the decision cadence (a rehearsal that lands after the send window is archaeology; near-real-time rollouts are what make simulate-first an operating order rather than a research project)")
    l=d.get("loop") or {}
    if not l.get("real_outcomes_compared_to_predictions"): f.append("SI-5 real outcomes are not compared with the simulated predictions (the loop closes only when what happened is scored against what the simulation said would happen)")
    if not l.get("prediction_error_recorded_and_fed_back"): f.append("SI-5 prediction error is not recorded and fed back into the simulation (an unscored simulation never improves; error records are the training signal for the next population revision)")
    if not l.get("finalists_confirmed_with_real_people"): f.append("SI-5 simulated winners go live with no real-person confirmation for high-risk decisions (simulation narrows options and stress-tests designs; when a decision carries real risk, the strongest option is still confirmed with real people before it is trusted)")
    if not l.get("outside_matches_inside_simulated_claims_exist_in_product"): f.append("SI-5 distribution shows interventions the product does not contain (what is shown outside must exist inside: a simulated win for a feature or wording the app does not actually deliver is a lie with extra steps)")
    return f
def main():
    d=json.load(open(sys.argv[1]))
    fails=check(d)
    for x in fails: print("FAIL", x)
    print(f"RESULT: {'PASS' if not fails else 'FAIL'} ({len(fails)} fails)")
    sys.exit(0 if not fails else 1)
if __name__=="__main__": main()
