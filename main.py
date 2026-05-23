"""
This module can be used to execute rpni learning algorithms.
"""

# ---------------- IMPORT ----------------
import state_merging
import helpers as hp
import automaton


# ---------------- EXAMPLES ----------------

run = {
    1: False,
    2: False,
    3: False,
    4: False,
    5: False,
}

# region >> 1: L = "words of length 3"
# DFA = BDFA

if run[1]:
    alphabet = {'a', 'b'}
    states = {'ε', '1', '2', '3', 'ρ'}
    transitions = {
        ('ε', 'a', '1'), ('ε', 'b', '1'),
        ('1', 'a', '2'), ('1', 'b', '2'),
        ('2', 'a', '3'), ('2', 'b', '3')
    }
    accepting_states = {'3'}
    automaton_1 = state_merging.make_automaton('length_3', states, alphabet, transitions, 'ε', accepting_states)
    pos_samples, neg_samples = state_merging.compute_rpni_complete_samples_for_dfa(automaton_1)
    state_merging.compare_learning(alphabet, pos_samples, neg_samples, state_merging.LearningConfig(state_merging.merge_with_rpni_order, 'type_1'), state_merging.LearningConfig(state_merging.merge_with_rpni_order, 'type_1'), name=automaton_1.name)

# endregion


# region >> 2: L = "all a's before all b's"
# DFA != BDFA

if run[2]:
    alphabet = {'a', 'b'}
    states = {'ε', 'b', 'ρ'}
    transitions = {
        ('ε', 'a', 'ε'), ('ε', 'b', 'b'),
        ('b', 'b', 'b')
    }
    accepting_states = {'ε', 'b'}
    automaton_2 = state_merging.make_automaton('all_as_before_all_bs', states, alphabet, transitions, 'ε', accepting_states)

    alphabet = {'a', 'b'}
    states = {'ε', 'a', 'b', 'ab', 'ρ'}
    r_transitions = {
        ('ε', 'a', 'a'), ('ε', 'b', 'b'),
        ('a', 'a', 'a'), ('a', 'b', 'ab'),
        ('b', 'b', 'b'),
        ('ab', 'b', 'ab')
    }
    l_transitions = {
        ('ε', 'a', 'a'), ('ε', 'b', 'b'),
        ('a', 'a', 'a'),
        ('b', 'b', 'b'), ('b', 'a', 'ab'),
        ('ab', 'a', 'ab')
    }
    accepting_states = {'ε', 'a', 'b', 'ab'}
    automaton_3 = state_merging.make_automaton('all_as_before_all_bs__monoid', states, alphabet, r_transitions, 'ε', accepting_states, l_transitions=l_transitions)

    # type_1: negative samples checked after each merge, sink does not need to be covered
    pos_samples_dfa, neg_samples_dfa = state_merging.compute_rpni_complete_samples_for_dfa(automaton_2, cover_sink=False)
    pos_samples_bdfa, neg_samples_bdfa = state_merging.compute_rpni_complete_samples_for_monoid(automaton_3, cover_sink=False)

    state_merging.compare_learning(alphabet, pos_samples_dfa, neg_samples_dfa, state_merging.LearningConfig(state_merging.merge_with_rpni_order, 'type_1'), state_merging.LearningConfig(state_merging.merge_with_rpni_order, 'type_1'), name=automaton_2.name + '_type1_dfasamples')
    state_merging.learn_monoid(alphabet, pos_samples_bdfa, neg_samples_bdfa, state_merging_algorithm=state_merging.merge_with_rpni_order, consistency_type='type_1', name=automaton_3.name + '_type1')

    # type_2: negative samples become rejecting states in the PTA, sink must be covered
    pos_samples_dfa, neg_samples_dfa = state_merging.compute_rpni_complete_samples_for_dfa(automaton_2, cover_sink=True)
    pos_samples_bdfa, neg_samples_bdfa = state_merging.compute_rpni_complete_samples_for_monoid(automaton_3, cover_sink=True)

    state_merging.compare_learning(alphabet, pos_samples_dfa, neg_samples_dfa, state_merging.LearningConfig(state_merging.merge_with_rpni_order, 'type_2'), state_merging.LearningConfig(state_merging.merge_with_rpni_order, 'type_2'), name=automaton_2.name + '_type2_dfasamples')
    state_merging.learn_monoid(alphabet, pos_samples_bdfa, neg_samples_bdfa, state_merging_algorithm=state_merging.merge_with_rpni_order, consistency_type='type_2', name=automaton_3.name + '_type2')

# endregion


# region >> 3: L = "all a's before all b's"
# samples without sink do not suffice for type_2

if run[3]:
    alphabet = {'a', 'b'}
    states = {'ε', 'b', 'ρ'}
    transitions = {
        ('ε', 'a', 'ε'), ('ε', 'b', 'b'),
        ('b', 'b', 'b')
    }
    accepting_states = {'ε', 'b'}
    automaton_2 = state_merging.make_automaton('all_as_before_all_bs', states, alphabet, transitions, 'ε', accepting_states)

    pos_samples, neg_samples = state_merging.compute_rpni_complete_samples_for_dfa(automaton_2, cover_sink=False)
    state_merging.learn_dfa(alphabet, pos_samples, neg_samples, state_merging.merge_with_rpni_order, 'type_2', name=automaton_2.name + '_consistency_type2')

# endregion


# region >> 4: L = "all a's before all b's"
# RPNI sample transfer: compute DFA samples for BDFA, map and use them to learn the BDFA

if run[4]:
    alphabet = {'a', 'b'}
    states = {'ε', 'b', 'ρ'}
    transitions = {
        ('ε', 'a', 'ε'), ('ε', 'b', 'b'),
        ('b', 'b', 'b')
    }
    accepting_states = {'ε', 'b'}
    automaton_2 = state_merging.make_automaton('all_as_before_all_bs', states, alphabet, transitions, 'ε', accepting_states)

    alphabet = {'a', 'b'}
    states = {'ε', 'a', 'b', 'ab', 'ρ'}
    r_transitions = {
        ('ε', 'a', 'a'), ('ε', 'b', 'b'),
        ('a', 'a', 'a'), ('a', 'b', 'ab'),
        ('b', 'b', 'b'),
        ('ab', 'b', 'ab')
    }
    l_transitions = {
        ('ε', 'a', 'a'), ('ε', 'b', 'b'),
        ('a', 'a', 'a'),
        ('b', 'b', 'b'), ('b', 'a', 'ab'),
        ('ab', 'a', 'ab')
    }
    accepting_states = {'ε', 'a', 'b', 'ab'}
    automaton_3 = state_merging.make_automaton('all_as_before_all_bs__monoid', states, alphabet, r_transitions, 'ε', accepting_states, l_transitions=l_transitions)

    state_merging.rpni_sample_transfer_from_dfa_to_monoid(alphabet, automaton_3, consistency_type='type_1', name=automaton_3.name)

# endregion


# region >> 5: L = "max length 2"
# for a finite L a sample can be constructed such that any merge order learns L
# when using merge algorithm of type 2

if run[5]:
    alphabet = {'a', 'b'}
    states = {'ε', '1', '2', 'ρ'}
    transitions = {
        ('ε', 'a', '1'), ('ε', 'b', '1'),
        ('1', 'a', '2'), ('1', 'b', '2')
    }
    accepting_states = {'ε', '1', '2'}
    ex_automaton = state_merging.make_automaton('up_to_length_2', states, alphabet, transitions, 'ε', accepting_states)
    pos_samples, neg_samples = state_merging.compute_merge_order_robust_samples_for_finite_L(ex_automaton)
    state_merging.learn_dfa(alphabet, pos_samples, neg_samples, state_merging.merge_with_random_order, 'type_1', name=ex_automaton.name + '_random_v1')
    state_merging.learn_dfa(alphabet, pos_samples, neg_samples, state_merging.merge_with_random_order, 'type_1', name=ex_automaton.name + '_random_v2')
    state_merging.learn_dfa(alphabet, pos_samples, neg_samples, state_merging.merge_with_random_order, 'type_1', name=ex_automaton.name + '_random_v3')

# endregion

