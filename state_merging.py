"""
This module contains the main functions for implementing the different state-merging algorithms
"""

# ---------------- IMPORT ----------------
import automaton
import helpers as hp

import copy
import time
import os
import shutil
from pathlib import Path
import itertools
from typing import Literal
from random import shuffle

# ---------------- FUNCTIONS ----------------
def compute_prefix_states(automaton):
    """
    Compute all states of the automaton that can reach a final state
    
    :param automaton: automaton

    :return: set of states that can reach an accepting state
    """

    queue = set(copy.deepcopy(automaton.accepting))
    reachable = set()

    while len(queue) > 0:
        current = queue.pop()

        # add reachable
        if current in reachable:
            continue
        reachable.add(current)

        # add all neighbors
        for transition in automaton.transitions:
            if transition[2] == current: # reversed transitions for inverted graph
                queue.add(transition[0])

    return reachable

def get_unreachable(automaton):
    """
    Compute all states of a given automaton that cannot be reached from the initial state
    
    :param automaton: automaton

    :return: set of states
    """

    reachable = set([automaton.initial])
    queue = [automaton.initial]

    # find reachable
    while len(queue) > 0:

        current = queue[0]
        reached = set()

        for transition in automaton.transitions:
            if transition[0] == current:
                reached.add(transition[2])
                
        queue = queue[1:] + list(reached.intersection(automaton.states.difference(reachable)))
        reachable = reachable.union(reached)

    # compute sink separately
    for state in automaton.states.difference({automaton.sink}):
        for letter in automaton.alphabet:
            if automaton.step(state, letter) == automaton.sink:
                reachable.add(automaton.sink)
                return automaton.states.difference(reachable)

    return automaton.states.difference(reachable)

def has_loop(automaton):
    """
    Checks if the given automaton has a loop

    :param automaton: automaton

    :return: truth value of computation
    """

    visited = set()
    on_stack = set()

    def dfs(state):
        visited.add(state)
        on_stack.add(state)

        for transition in automaton.transitions:
            if transition[0] == state:
                neighbor = transition[2]
                if neighbor in on_stack:
                    return True
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True

        on_stack.discard(state)
        return False

    for state in automaton.states:
        if state not in visited:
            if dfs(state):
                return True

    return False


def remove_unreachable(automaton):
    """
    Remove all states of a given automaton that cannot be reached from the initial state
    
    :param automaton: automaton

    :return: modified automaton
    """

    unreachable = get_unreachable(automaton)
    for state in unreachable:
        if state != automaton.sink:
            automaton.remove_state(state)

    return automaton

def compute_product_automaton(automaton1, automaton2, acceptance_type: Literal['both_accepting', 'one_accepting', 'none_accepting'] = 'both_accepting', cleanup = False):
    """
    Compute product automaton of two initial automatons.
    
    :param automaton1: automaton
    :param automaton2: automaton
    :param acceptance_type: decides which states of the product automaton are accepting

    :return: product automaton
    """

    if automaton1.alphabet != automaton2.alphabet:
        return None

    product_automaton = automaton.Automaton(name='product_automaton')
    product_automaton.set_alphabet(automaton1.alphabet)

    states = set()
    initial = ''
    sink = ''
    accepting = set()
    transitions = set()

    for state1 in automaton1.states:
        for state2 in automaton2.states:

            # new state
            state = '{' + state1 + ',' + state2 + '}'
            states.add(state)

            # track initial
            if state1 == automaton1.initial and state2 == automaton2.initial: 
                initial = state

            # add to accepting
            if acceptance_type == 'both_accepting' and state1 in automaton1.accepting and state2 in automaton2.accepting:
                accepting.add(state)

            if acceptance_type == 'one_accepting' and (state1 in automaton1.accepting) != (state2 in automaton2.accepting):
                accepting.add(state)

            if acceptance_type == 'none_accepting' and state1 not in automaton1.accepting and state2 not in automaton2.accepting:
                accepting.add(state)

            # track sink
            if state1 == automaton1.sink and state2 == automaton2.sink: 
                sink = state

            # compute transitions
            transitions_to_combine = dict(zip(list(automaton1.alphabet), [list() for i in range(0, len(automaton1.alphabet))]))

            for transition in automaton1.transitions:
                if transition[0] == state1:
                    transitions_to_combine[transition[1]].append(transition[2])

            for letter in transitions_to_combine:
                if len(transitions_to_combine[letter]) == 0:
                    transitions_to_combine[letter].append(automaton1.sink)

            for transition in automaton2.transitions:
                if transition[0] == state2:
                    transitions_to_combine[transition[1]].append(transition[2])

            for letter in transitions_to_combine:
                if len(transitions_to_combine[letter]) == 1:
                    transitions_to_combine[letter].append(automaton2.sink)

            for letter in transitions_to_combine:
                goal_state = '{' + transitions_to_combine[letter][0] + ',' + transitions_to_combine[letter][1] + '}'
                transitions.add((state, letter, goal_state))

    product_automaton.set_states(states)
    product_automaton.set_initial(initial)
    product_automaton.set_sink(sink)

    for accepting_state in accepting:
        product_automaton.add_accepting_state(accepting_state)
    for transition in transitions:
        product_automaton.add_transition(transition[0], transition[1], transition[2])

    if cleanup:
        product_automaton = remove_unreachable(product_automaton)

    return product_automaton


def shortest_accepting_suffix(automaton, source_state, has_lr_alphabet=False):
    """
    Find the shortest suffix that reaches a final state from the given source state

    :param automaton: automaton
    :param source_state: state to start run from
    :param has_lr_alphabet: if automaton has LR alphabet

    :return: suffix word whose run goes from the source_state to an accepting state
    """

    queue = [source_state]
    visited = set([source_state])
    parent = dict()

    while queue:

        current = queue[0]
        queue = queue[1:]

        # if accepting reached, reconstruct suffix
        if current in automaton.accepting:
            reached = current
            suffix = []
            while current != source_state:
                current, letter = parent[current]
                suffix.append(letter)
            return ''.join(reversed(suffix)), reached
        
        # get all transitions from current state
        transitions = []
        for transition in automaton.transitions:
            if transition[0] == current:
                transitions.append(transition)

        transitions.sort(key=lambda t: hp.canonical_word_key(t[1], automaton.alphabet, is_lr=has_lr_alphabet))

        # check transitions to other states in canonical order
        for transition in transitions:
            if transition[2] not in visited:
                visited.add(transition[2])
                parent[transition[2]] = (current, transition[1])
                queue.append(transition[2])

    return None, None

def shortest_accepting_prefix_and_suffix_for_monoids(automaton, source_state):
    """
    Find the shortest path that reaches a final state from the given source state,
    input is a BDFA so the path can be reconstructed to a prefix and suffix word

    :param automaton: automaton
    :param source_state: state to start run from

    :return: prefix and suffix words whose run on the BDFA reaches a final state
    """

    queue = [source_state]
    visited = set([source_state])
    parent = dict()

    while queue:
        
        current = queue[0]
        queue = queue[1:]

        # if accepting reached, reconstruct automaton suffix which translates to word prefix and suffix
        if current in automaton.accepting:
            reached = current
            letters = []
            prefix, suffix = [], []
            while current != source_state:
                current, letter = parent[current]
                letters.append(letter)

                # divide in left and right transitions for prefix and suffix
                if '[l]' in letter:
                    prefix.append(letter.replace('[l]', ''))
                if '[r]' in letter:
                    suffix.append(letter.replace('[r]', ''))

            return ''.join(prefix), ''.join(reversed(suffix)), reached
        
        # get all transitions from current state
        transitions = []
        for transition in automaton.transitions:
            if transition[0] == current:
                transitions.append(transition)
        transitions.sort(key=lambda t: t[1])

        # check transitions to other states in canonical order
        for transition in transitions:
            if transition[2] not in visited:
                visited.add(transition[2])
                parent[transition[2]] = (current, transition[1])
                queue.append(transition[2])

    return None, None, None


def compute_rpni_minimal_representatives_for_dfa(automaton, cover_sink=False, has_lr_alphabet=False):
    """
    Compute minimal representatives MR(L) and minimal transition representatives MTR(L) for a minimal automaton 
    recognizing the language L with respect to the RPNI algorithm+
    
    :param automaton: automaton

    :return: tuple of minimal representative set and minimal transition representative set
    """

    mr_l = []
    mtr_l = []

    # when iterating states, skip the ones that cannot reach a final state
    prefix_states = compute_prefix_states(automaton)
    unreachable = automaton.states.difference(prefix_states)

    states_to_cover = list(copy.deepcopy(automaton.states).union({automaton.sink}).difference(unreachable))
    states_to_cover.sort(key=lambda t: hp.canonical_word_key(t, automaton.alphabet))
 
    covered_sink = not cover_sink or automaton.sink in unreachable

    i = 0
    while len(states_to_cover) > 0 or not covered_sink:

        # try words in canonical order upwards in length
        words = hp.words_of_length_x(automaton.alphabet, i, has_lr_alphabet=has_lr_alphabet)

        for word in words:

            final_state = automaton.run_and_return_state(word, verbose=False)

            # if word is first to reach this state, save it
            if final_state in states_to_cover:
                mr_l.append(word)
                states_to_cover.remove(final_state)

            elif final_state == automaton.sink and not covered_sink:
                mr_l.append(word)
                covered_sink = True

            if len(states_to_cover) == 0 and covered_sink:
                break
        i += 1

    # for each minimal representative, add each possible transition word, if it can be accepted with any suffix
    for rep in mr_l:

        alphabet = list(automaton.alphabet)
        alphabet.sort(key=lambda t: hp.canonical_word_key(t, automaton.alphabet, is_lr=has_lr_alphabet))

        for letter in alphabet:

            final_state = automaton.run_and_return_state(rep + letter, verbose=False)
            if final_state in prefix_states or cover_sink:
                mtr_l.append(rep + letter)

    mtr_l.append('') # if we use only MTR for first sample condition this is necessary (this way MR is subset of MTR)

    mr_l = list(set(mr_l))
    mr_l.sort(key=lambda t: hp.canonical_word_key(t, automaton.alphabet, is_lr=has_lr_alphabet))
    mtr_l = list(set(mtr_l))
    mtr_l.sort(key=lambda t: hp.canonical_word_key(t, automaton.alphabet, is_lr=has_lr_alphabet))

    return mr_l, mtr_l

def compute_rpni_complete_samples_for_dfa(automaton, cover_sink=False, has_lr_alphabet=False):
    """
    Compute RPNI-complete positive and negative samples as input for the algorithm to learn a language L,
    using a given minimal dfa that recognizes the language
    
    :param automaton: automaton

    :return: tuple of negative sample and positive sample set
    """

    pos_samples, neg_samples = set(), set()
    mr_l, mtr_l = compute_rpni_minimal_representatives_for_dfa(automaton, cover_sink=cover_sink, has_lr_alphabet=has_lr_alphabet)
    prefix_states = compute_prefix_states(automaton)

    # cover all final states in positive samples
    # for word in mr_l:
    #    if automaton.run(word, verbose=False):
    #        pos_samples.add(word)

    # cover all transitions in positive samples
    for word in mtr_l:
        final_state = automaton.run_and_return_state(word, verbose=False)

        # representative is already a word of L
        if final_state in automaton.accepting:
            pos_samples.add(word)

        # add shortest suffix to representative so it is part of L
        elif final_state in prefix_states:
            suffix, accepting_state = shortest_accepting_suffix(automaton, final_state, has_lr_alphabet=has_lr_alphabet)
            pos_samples.add(word + suffix)

    # separate words of different equivalence classes
    for mr in mr_l:
        for mtr in mtr_l:

            finalstate_mr = automaton.run_and_return_state(mr, verbose=False)
            finalstate_mtr = automaton.run_and_return_state(mtr, verbose=False)

            if finalstate_mr == finalstate_mtr:
                continue
            else:

                # only one word of the pair is accepted, so we can use it for the samples
                if (finalstate_mr in automaton.accepting and finalstate_mtr not in automaton.accepting):
                    pos_samples.add(mr)
                    neg_samples.add(mtr)
                   
                elif (finalstate_mr not in automaton.accepting and finalstate_mtr in automaton.accepting):
                    neg_samples.add(mr)
                    pos_samples.add(mtr)
                    
                # find a suffix for both words, so only one is accepted, use those for samples
                else:

                    # make product automaton from original, each one has as initial state the final state of the mr or mtr sample
                    automaton_mr = copy.deepcopy(automaton)
                    automaton_mr.set_initial(finalstate_mr)

                    automaton_mtr = copy.deepcopy(automaton)
                    automaton_mtr.set_initial(finalstate_mtr)

                    product_automaton = compute_product_automaton(automaton_mr, automaton_mtr, acceptance_type='one_accepting')

                    # find shortest suffix to goal state that consists of only one original accepting state
                    start = '{' + finalstate_mr + ',' + finalstate_mtr + '}'
                    suffix, accepting_state = shortest_accepting_suffix(product_automaton, start, has_lr_alphabet=has_lr_alphabet)

                    goal_mr, goal_mtr = (accepting_state[1:len(accepting_state)-1]).split(',', 1)

                    # split up in positive and negative sample
                    if goal_mr in automaton.accepting and goal_mtr not in automaton.accepting:
                        pos_samples.add(mr + suffix)
                        neg_samples.add(mtr + suffix)

                    elif goal_mr not in automaton.accepting and goal_mtr in automaton.accepting:
                        neg_samples.add(mr + suffix)
                        pos_samples.add(mtr + suffix)

    pos_samples = list(set(pos_samples))
    pos_samples.sort(key=lambda t: hp.canonical_word_key(t, automaton.alphabet, is_lr=has_lr_alphabet))
    neg_samples = list(set(neg_samples))
    neg_samples.sort(key=lambda t: hp.canonical_word_key(t, automaton.alphabet, is_lr=has_lr_alphabet))

    return pos_samples, neg_samples


def compute_rpni_minimal_representatives_for_monoid(automaton, cover_sink=False):
    """
    Compute minimal representatives MR(L) and minimal transition representatives MTR(L) for the syntactic monoid 
    recognizing the language L with respect to the RPNI algorithm+
    
    :param automaton: automaton
    :param cover_sink: include representatives for sink state

    :return: tuple of minimal representative set and minimal transition representative set
    """

    mr_l = []
    mtr_l = []

    # reconstruct alphabet without left/right transitions
    true_alphabet = hp.get_normal_alphabet_from_lr(automaton.alphabet)

    # when iterating states, skip the ones that cannot reach a final state
    prefix_states = compute_prefix_states(automaton)
    unreachable = automaton.states.difference(prefix_states)

    states_to_cover = list(copy.deepcopy(automaton.states).union({automaton.sink}).difference(unreachable))
    states_to_cover.sort(key=lambda t: hp.canonical_word_key(t, true_alphabet))
 
    covered_sink = not cover_sink or automaton.sink in unreachable

    i = 0
    while len(states_to_cover) > 0 or not covered_sink:

        # try words in canonical order upwards in length
        words = hp.words_of_length_x(true_alphabet, i)
        for word in words:

            final_state = automaton.run_and_return_state_as_bdfa(word, verbose=False)

            # if word is first to reach this state, save it
            if final_state in states_to_cover:
                mr_l.append(word)
                states_to_cover.remove(final_state)

            elif final_state == automaton.sink and not covered_sink:
                mr_l.append(word)
                covered_sink = True

            if len(states_to_cover) == 0 and covered_sink:
                break
        i += 1

    # for each minimal representative, add each possible transition word, if accepted
    true_alphabet = sorted(true_alphabet, key=lambda t: hp.canonical_word_key(t, true_alphabet))
    for rep in mr_l:

        for letter in true_alphabet:

            # left transitions
            final_state = automaton.run_and_return_state_as_bdfa(rep + letter, verbose=False)
            if final_state in prefix_states or cover_sink:
                mtr_l.append(rep + letter)

            # right transitions
            final_state = automaton.run_and_return_state_as_bdfa(letter + rep, verbose=False)
            if final_state in prefix_states or cover_sink:
                mtr_l.append(letter + rep)
        
    mtr_l.append('') # if we use only MTR for first sample condition this is necessary (this way MR is subset of MTR)

    mr_l = list(set(mr_l))
    mr_l.sort(key=lambda t: hp.canonical_word_key(t, true_alphabet))
    mtr_l = list(set(mtr_l))
    mtr_l.sort(key=lambda t: hp.canonical_word_key(t, true_alphabet))
    
    return mr_l, mtr_l

def compute_rpni_complete_samples_for_monoid(automaton, cover_sink=False):
    """
    Compute RPNI-complete positive and negative samples as input for the algorithm to learn a language L,
    using the given syntactic monoid that recognizes L
    
    :param automaton: automaton
    :param cover_sink: include samples for sink state

    :return: tuple of negative sample and positive sample set
    """

    # reconstruct alphabet without left/right transitions
    true_alphabet = hp.get_normal_alphabet_from_lr(automaton.alphabet)

    pos_samples, neg_samples = set(), set()
    mr_l, mtr_l = compute_rpni_minimal_representatives_for_monoid(automaton, cover_sink=cover_sink)
    prefix_states = compute_prefix_states(automaton)

    # cover all final states in positive samples
    # for word in mr_l:
    #     if automaton.run_as_bdfa(word, verbose=False):
    #         pos_samples.add(word)

    # cover all transitions in positive samples
    for word in mtr_l:
        final_state = automaton.run_and_return_state_as_bdfa(word, verbose=False)

        # representative is already a word of L
        if final_state in automaton.accepting:
            pos_samples.add(word)

        # add shortest prefix and suffix to representative so it is part of L
        elif final_state in prefix_states:

            prefix, suffix, accepting_state = shortest_accepting_prefix_and_suffix_for_monoids(automaton, final_state)
            pos_samples.add(prefix + word + suffix)

    # separate words of different equivalence classes
    for mr in mr_l:
        for mtr in mtr_l:

            finalstate_mr = automaton.run_and_return_state_as_bdfa(mr, verbose=False)
            finalstate_mtr = automaton.run_and_return_state_as_bdfa(mtr, verbose=False)

            if finalstate_mr == finalstate_mtr:
                continue
            else:
                # only one word of the pair is accepted, so we can use it for the samples
                if (finalstate_mr in automaton.accepting and finalstate_mtr not in automaton.accepting):
                    pos_samples.add(mr)
                    neg_samples.add(mtr)
                   
                elif (finalstate_mr not in automaton.accepting and finalstate_mtr in automaton.accepting):
                    neg_samples.add(mr)
                    pos_samples.add(mtr)
                    
                # both words end in the same class — find a prefix and suffix that separates them
                else:

                    # make product automaton from original, each one has as initial state the final state of the mr or mtr sample
                    automaton_mr = copy.deepcopy(automaton)
                    automaton_mr.set_initial(finalstate_mr)

                    automaton_mtr = copy.deepcopy(automaton)
                    automaton_mtr.set_initial(finalstate_mtr)

                    product_automaton = compute_product_automaton(automaton_mr, automaton_mtr, acceptance_type='one_accepting')

                    # find shortest prefix and suffix to goal state that consists of only one original accepting state
                    start = '{' + finalstate_mr + ',' + finalstate_mtr + '}'
                    prefix, suffix, accepting_state = shortest_accepting_prefix_and_suffix_for_monoids(product_automaton, start)

                    goal_mr, goal_mtr = (accepting_state[1:len(accepting_state)-1]).split(',', 1)

                    # split up in positive and negative sample
                    if goal_mr in automaton.accepting and goal_mtr not in automaton.accepting:
                        pos_samples.add(prefix + mr + suffix)
                        neg_samples.add(prefix + mtr + suffix)

                    if goal_mr not in automaton.accepting and goal_mtr in automaton.accepting:
                        neg_samples.add(prefix + mr + suffix)
                        pos_samples.add(prefix + mtr + suffix)

    pos_samples = list(set(pos_samples))
    pos_samples.sort(key=lambda t: hp.canonical_word_key(t, true_alphabet))
    neg_samples = list(set(neg_samples))
    neg_samples.sort(key=lambda t: hp.canonical_word_key(t, true_alphabet))

    return pos_samples, neg_samples


def compute_exponential_samples_by_n(automaton, n, is_bdfa=False):
    """
    Compute positive and negative samples for the given automaton up to some length n
    
    :param automaton: automaton
    :param n: max length
    :param is_bdfa: if automaton is a BDFA

    :return: tuple of negative sample and positive sample list
    """

    true_alphabet = set()
    if is_bdfa:
        true_alphabet = hp.get_normal_alphabet_from_lr(automaton.alphabet)
    else:
        true_alphabet = automaton.alphabet

    samples = ['']
    for i in range(1, n+1):
        samples += hp.words_of_length_x(true_alphabet, i)

    pos_samples, neg_samples = [], []

    for sample in samples:
        result = automaton.run_as_bdfa(sample, verbose=False) if is_bdfa else automaton.run(sample, verbose=False)
        if result:
            pos_samples.append(sample)
        else:
            neg_samples.append(sample)

    return pos_samples, neg_samples

def compute_exponential_samples_by_n_given_L(l, n, alphabet):
    """
    Compute positive and negative samples for the given language up to some length n
    
    :param l: set of all words in l
    :param n: max length

    :return: tuple of negative sample and positive sample list
    """

    all_samples = ['']

    for i in range(1, n+1):
        all_samples += hp.words_of_length_x(alphabet, i)

    pos_samples, neg_samples = set(all).intersection(set(l)), set(all).difference(set(l))
    return list(pos_samples), list(neg_samples)

def compute_merge_order_robust_samples_for_finite_L(automaton, is_bdfa=False):
    """
    Compute positive and negative samples for the given automaton such that the finite language can be learned by a state-merging 
    algorithm with any merge order
    
    :param automaton: automaton
    :param is_bdfa: if automaton is a BDFA

    :return: tuple of negative sample and positive sample list
    """

    if has_loop(automaton):
        return [], []

    state_count = len(automaton.states)
    n = state_count + (state_count * state_count)
    
    return compute_exponential_samples_by_n(automaton, n, is_bdfa=is_bdfa)

def compute_merge_order_robust_samples_for_finite_L_given_L(l, alphabet):
    """
    Compute positive and negative samples for the given language such that the finite language can be learned by a state-merging 
    algorithm with any merge order
    
    :param l: set of all words in l
    :param alphabet: alphabet of the language

    :return: tuple of negative sample and positive sample list
    """

    state_count = len(max(l, key=len))
    n = state_count + (state_count * state_count)
    
    return compute_exponential_samples_by_n_given_L(l, n, alphabet)


def make_automaton(name, states, alphabet, r_transitions, initial_state, final_states, l_transitions=set()):
    """
    Initializes an automaton object with the given parameters, generates a BDFA when left transitions are given
    
    :param name: automaton name
    :param states: state set
    :param alphabet: alphabet
    :param r_transitions: set of triples as right transitions
    :param initial_state: initial state
    :param final_states: final states
    :param l_transitions: set of triples as left transitions

    :return: automaton
    """
 
    transitions = set()
    if l_transitions != None and len(l_transitions) > 0:
        alphabet = hp.get_lr_alphabet(alphabet)
        for transition in r_transitions:
            transitions.add((transition[0], transition[1] + '[r]', transition[2]))
        for transition in l_transitions:
            transitions.add((transition[0], transition[1] + '[l]', transition[2]))
    else:
        transitions = r_transitions

    new_automaton = automaton.Automaton(name)

    new_automaton.set_states(states)
    new_automaton.set_alphabet(alphabet)

    for transition in transitions:
        new_automaton.add_transition(transition[0], transition[1], transition[2])

    new_automaton.set_initial(initial_state)

    for state in final_states:
        new_automaton.add_accepting_state(state)

    return new_automaton

def make_prefix_automaton(positive_samples, alphabet, negative_samples=[]):
    """
    Create PTA accepting exactly a list of words. If negative samples are given as well, an EPTA is constructed with rejecting states

    :param samples: list of prefixes to accept
    :param alphabet: automaton alphabet
    :param negative_samples: set of negative samples

    :return: prefix automaton
    """

    prefix_automaton = automaton.Automaton(name='prefix_automaton')
    prefix_automaton.set_alphabet(alphabet=alphabet)

    # iterate samples
    for sample in set(positive_samples).union(set(negative_samples)):

        previous_state = prefix_automaton.initial
        prefix = ''
        iterated_sample = sample

        current_letter = ''
        while True:
            current_letter, iterated_sample = hp.get_next_letter(iterated_sample, alphabet)
            if current_letter is None:
                break

            prefix += current_letter
            next_state = prefix_automaton.step(previous_state=previous_state, letter=current_letter)

            # if automaton goes to sink, add state and transition for this step
            if (next_state == prefix_automaton.sink):

                next_state = prefix
                prefix_automaton.add_state(next_state)
                prefix_automaton.add_transition(previous_state, current_letter, next_state)

            previous_state = next_state

        # accepting/rejecting step when sample input is complete
        if sample in positive_samples:
            prefix_automaton.add_accepting_state(previous_state)
        if sample in negative_samples:
            prefix_automaton.add_rejecting_state(previous_state)

    return prefix_automaton

def make_infix_automaton(positive_samples, alphabet, negative_samples=[]):
    """
    Create an infix automaton using left and right transitions accepting exactly a list of words. If negative
    samples are given as well, an extended infix automaton is constructed with rejecting states

    :param positive_samples: list of words to accept
    :param alphabet: automaton alphabet
    :param negative_samples: list of words to reject

    :return: infix automaton
    """

    # compute alphabet with left and right transitions
    complete_alphabet = set()
    for letter in alphabet:
        complete_alphabet.add(letter + '[l]')
        complete_alphabet.add(letter + '[r]')

    infix_automaton = automaton.Automaton(name='infix_automaton')
    infix_automaton.set_alphabet(alphabet=complete_alphabet)
    prefixes = set()

    # prefix automaton, iterate samples
    for sample in set(positive_samples).union(set(negative_samples)):

        previous_state = infix_automaton.initial
        prefix = ''

        # compute steps for sample
        for char in sample:
            prefix += char
            next_state = infix_automaton.step(previous_state=previous_state, letter=char + '[r]')

            # if automaton goes to sink, add state and transition for this step
            if (next_state == infix_automaton.sink):

                next_state = prefix
                infix_automaton.add_state(next_state)
                infix_automaton.add_transition(previous_state, char + '[r]', next_state)

                prefixes.add(prefix)

            previous_state = next_state

        # accepting/rejecting step when sample input is complete
        if (sample in positive_samples):
            infix_automaton.add_accepting_state(previous_state)
        elif (sample in negative_samples):
            infix_automaton.add_rejecting_state(previous_state)

    # add all possible suffixes of samples as states
    for prefix in prefixes:
        for i in range(1, len(prefix)):
            infix_state = prefix[i:]

            if infix_state not in infix_automaton.states:
                infix_automaton.add_state(infix_state)

    # complete transitions between new states
    for state in infix_automaton.states.difference({infix_automaton.sink}):
        for char in alphabet:

            next_l = infix_automaton.step(previous_state=state, letter=char + '[l]')
            next_r = infix_automaton.step(previous_state=state, letter=char + '[r]')
            infix = state

            # if left transition goes to sink, add transition for this step
            if next_l == infix_automaton.sink:
                next_state_should_be = char + (infix if state != infix_automaton.initial else '')

                if next_state_should_be in infix_automaton.states:
                    infix_automaton.add_transition(state, char + '[l]', next_state_should_be)

            # if right transition goes to sink, add transition for this step
            if next_r == infix_automaton.sink:
                next_state_should_be = (infix if state != infix_automaton.initial else '') + char

                if next_state_should_be in infix_automaton.states:
                    infix_automaton.add_transition(state, char + '[r]', next_state_should_be)

    return infix_automaton


def merge_states(automaton, state1, state2):
    """
    Merge two automaton states according to merging algorithm strategies:
    After merging check if new states and transitions imply other states need to be merged as well,
    merge until no more merges found.
    Compute new automaton and merges executed

    :param automaton: automaton
    :param state1: part of initial state pair to merge
    :param state2: part of initial state pair to merge

    :return: automaton after merges, set of merge tuples
    """

    if state1 == state2:
        return
    
    merger = state1
    mergee = state2

    executed_merges = [] 
    future_merges = set()
    accepting_and_rejecting = []

    automaton_prestep = copy.deepcopy(automaton)
    automaton_poststep = copy.deepcopy(automaton)

    while True:

        # for current state tuple: remove states from automaton and from future merges
        removed_transitions = automaton_poststep.remove_state(merger)
        removed_transitions = removed_transitions.union(automaton_poststep.remove_state(mergee)) 

        future_merges, removed_merges = hp.remove_merges(future_merges, merger)
        future_merges, removed_merges2 = hp.remove_merges(future_merges, mergee)

        # add new merged state to automaton (minding initial and final states) and to future merges
        merged_state = hp.compute_merge_name(merger, mergee, automaton.alphabet)
        automaton_poststep.add_state(merged_state)
        executed_merges.append((merger, mergee, merged_state))

        if merger == automaton_prestep.initial or mergee == automaton_prestep.initial:
            automaton_poststep.set_initial(merged_state)

        if merger in automaton_prestep.accepting or mergee in automaton_prestep.accepting:
            automaton_poststep.add_accepting_state(merged_state)

            if merger in automaton_prestep.rejecting:
                accepting_and_rejecting.append(merged_state)

            if mergee in automaton_prestep.rejecting:
                accepting_and_rejecting.append(merged_state)

        elif merger in automaton_prestep.rejecting or mergee in automaton_prestep.rejecting:
            automaton_poststep.add_rejecting_state(merged_state)

        # future merges involving the current states are filtered
        for merge in removed_merges.union(removed_merges2):

            # merge already happened
            if (merge[0] == merger or merge[0] == mergee) and (merge[1] == merger or merge[1] == mergee):
                continue

            # merge needs to be modified, because one state was already merged
            if (merge[0] == merger or merge[0] == mergee):
                future_merges.add((merged_state, merge[1]))

            if (merge[1] == merger or merge[1] == mergee):
                future_merges.add((merge[0], merged_state))

        # add new transitions for states
        new_transitions = set()
        for transition in removed_transitions:
            new_transition = (
                merged_state if (transition[0] == merger or transition[0] == mergee) else transition[0],
                transition[1],
                merged_state if (transition[2] == merger or transition[2] == mergee) else transition[2]
            )

            if new_transition not in new_transitions:
                new_transitions.add(new_transition)
                automaton_poststep.add_transition(new_transition[0], new_transition[1], new_transition[2])

        # find states that need to be merged too
        for transition in new_transitions:
            for transition2 in new_transitions:

                # two transitions have same letter and source state, so goal states must be merged
                if (transition != transition2 and transition[0] == transition2[0] and transition[1] == transition2[1]):
                    if (transition[2] < transition2[2]):
                        future_merges.add((transition[2], transition2[2]))
                    else:
                        future_merges.add((transition2[2], transition[2]))


        automaton_prestep = copy.deepcopy(automaton_poststep)

        # prepare next merge
        if len(future_merges) > 0:

            next_merge = future_merges.pop()
            merger = next_merge[0]
            mergee = next_merge[1]

        # no more merges to do
        else:
            break


    return automaton_poststep, executed_merges, accepting_and_rejecting
    
def get_right_cayley_graph_from_bdfa(automaton):
    """
    Get right cayley graph from BDFA by removing left transitions

    :param automaton: BDFA

    :return: right cayley graph as automaton
    """

    cayley = copy.deepcopy(automaton)

    transitions_from_by_state = dict()
    transitions_to_by_state = dict()

    transitions_to_remove = set()
    states_to_remove = set()

    for transition in cayley.transitions:

        # remove left transitions
        if '[r]' not in transition[1]:
            transitions_to_remove.add(transition)

        # for right transitions, sort them by source and goal state
        else:
            if transition[0] not in transitions_from_by_state:
                transitions_from_by_state[transition[0]] = set()
            transitions_from_by_state[transition[0]].add(transition)

            if transition[2] not in transitions_to_by_state:
                transitions_to_by_state[transition[2]] = set()
            transitions_to_by_state[transition[2]].add(transition)

    # if state is isolated after removing transitions, remove that state too
    for state in cayley.states:
        from_transitions = set() if state not in transitions_from_by_state else transitions_from_by_state[state]
        to_transitions = set() if state not in transitions_to_by_state else transitions_to_by_state[state]

        if len(from_transitions) == 0 and len(to_transitions) == 0:
            states_to_remove.add(state)

    for state in states_to_remove:
        cayley.remove_state(state)

    for transition in transitions_to_remove:
        cayley.remove_transition(transition[0], transition[1], transition[2])

    return cayley

def get_left_cayley_graph_from_bdfa(automaton):
    """
    Get left cayley graph from BDFA by removing right transitions

    :param automaton: BDFA

    :return: left cayley graph as automaton
    """

    cayley = copy.deepcopy(automaton)

    transitions_from_by_state = dict()
    transitions_to_by_state = dict()

    transitions_to_remove = set()
    states_to_remove = set()

    for transition in cayley.transitions:

        # remove right transitions
        if '[l]' not in transition[1]:
            transitions_to_remove.add(transition)

        # for left transitions, sort them by source and goal state
        else:
            if transition[0] not in transitions_from_by_state:
                transitions_from_by_state[transition[0]] = set()
            transitions_from_by_state[transition[0]].add(transition)

            if transition[2] not in transitions_to_by_state:
                transitions_to_by_state[transition[2]] = set()
            transitions_to_by_state[transition[2]].add(transition)

    # if state is isolated after removing transitions, remove that state too
    for state in cayley.states:
        from_transitions = set() if state not in transitions_from_by_state else transitions_from_by_state[state]
        to_transitions = set() if state not in transitions_to_by_state else transitions_to_by_state[state]

        if len(from_transitions) == 0 and len(to_transitions) == 0:
            states_to_remove.add(state)

    for state in states_to_remove:
        cayley.remove_state(state)

    for transition in transitions_to_remove:
        cayley.remove_transition(transition[0], transition[1], transition[2])

    return cayley


def merge_with_rpni_order(automaton, neg_samples, path='', is_bdfa=False, has_lr_alphabet=False):
    """
    Executes rpni algorithm in automaton using negative samples and accepting/rejecting states, saves detailed output and rendered automaton steps

    :param automaton: automaton to execute algorithm on
    :param neg_samples: list of negative samples
    :param path: file path to save output under
    :param is_bdfa: if input is a BDFA
    :param has_lr_alphabet: if input is over LR alphabet (relevant for sorting)

    :return: automaton after merges
    """
  
    merge_map = []

    if path == '':  path = '/output/rpni/' 
    automaton.draw(path=path + '_initial_automaton')

    sorted_states = list(automaton.states.difference({automaton.sink}))
    sorted_states.sort(key=lambda t: hp.canonical_word_key(t, automaton.alphabet, is_lr=has_lr_alphabet))

    for i in range(1, len(sorted_states)):

        merge_was_success = False
        for j in range(0, i):

            # map state pair to correct states after merges
            state_i = hp.map_merge(sorted_states[i], merge_map)
            state_j = hp.map_merge(sorted_states[j], merge_map)

            if state_i == state_j:
                continue

            # prepare output
            index_i = str(i).zfill(3)
            index_j = str(j).zfill(3)

            word_i = sorted_states[i]
            word_j = sorted_states[j]

            save_file_prefix = path + index_i + '-' + index_j
            reference = '(' + index_i + '-' + index_j + ')'

            # check if already merged
            if state_i.split('_')[0] != word_i:

                hp.save_to_text_file(
                    ['>> [NO]: ROOT MERGE ' + state_i + ' (' + word_i + ')' + ' & ' + state_j + ' (' + word_j + ') ' + reference,
                     '--> ' + state_i + ' was already merged with smaller state'],
                    save_file_prefix + '_not_merged.txt'
                )
                break
            
            # merge pair
            new_automaton, merges, accepting_and_rejecting = merge_states(automaton, state_i, state_j)

            # check if negative sample is accepted
            neg_sample_accepted = None
            for neg_sample in neg_samples:

                result = new_automaton.run(neg_sample, verbose=False) if not is_bdfa else new_automaton.run_as_bdfa(neg_sample, verbose=False)
                if result:
                    neg_sample_accepted = neg_sample
                    break

            # more output
            print_array = ['ROOT MERGE ' + state_i + ' (' + word_i + ')' + ' & ' + state_j + ' (' + word_j + ') ' + reference,
                           '\n',
                           'MERGES THAT FOLLOWED:',
                           str(merges), 
                           '\n',
                           'TO RECEIVE THIS SET OF STATES:', 
                           str(new_automaton.states)]

            # merge accepted negative sample
            if neg_sample_accepted is not None:

                print_array[0] = '>> [NO]: ' + print_array[0]
                print_array = print_array + ['\n', 'MERGES NOT EXECUTED BECAUSE THE FOLLOWING NEGATIVE SAMPLE WAS ACCEPTED:', str(neg_sample_accepted)]
                hp.save_to_text_file(print_array, save_file_prefix + '_not_merged.txt')

            # merge combined accepting and rejecting state
            elif len(accepting_and_rejecting) > 0:

                print_array[0] = '>> [NO]: ' + print_array[0]
                print_array = print_array + ['\n', 'MERGES NOT EXECUTED BECAUSE THE FOLLOWING STATES ARE ACCEPTING AND REJECTING:', str(accepting_and_rejecting)]
                hp.save_to_text_file(print_array, save_file_prefix + '_not_merged.txt')

            # merge was successful, document merge result 
            else:
                automaton = copy.deepcopy(new_automaton)

                print_array[0] = '>> [YES]: ' + print_array[0]
                hp.save_to_text_file(print_array, save_file_prefix + '_merged.txt')

                automaton.draw(path=save_file_prefix + '_automaton')
                
                # update merge map
                for merge in merges:
                    if merge not in merge_map:
                        merge_map.append(merge)

                merge_was_success = True

            # if merged, move on to next state
            if merge_was_success:
                break

    automaton.draw(include_sink=False, path=path + 'result', verbose=False)

    automaton.name = 'minimal'
    return automaton

def merge_with_random_order(automaton, neg_samples, path='', is_bdfa=False):
    """
    Executes state merging algorithm with random merge order using negative samples and accepting/rejecting, saves detailed output and rendered automaton steps

    :param automaton: automaton to execute algorithm on
    :param neg_samples: list of negative samples
    :param path: file path to save output under
    :param is_bdfa: if input is a BDFA

    :return: automaton after random merges
    """
  
    merge_map = []

    if path == '':  path = '/output/rpni/' 
    automaton.draw(path=path + '_initial_automaton')

    i = 0
    while True:
        current_state_set = list(automaton.states.difference({automaton.sink}))
        pairs = list(itertools.combinations(current_state_set, 2))
        shuffle(pairs)

        merged, j = False, 0
        for pair in pairs:
            
            # map state pair to correct states after merges
            state_i = hp.map_merge(pair[0], merge_map)
            state_j = hp.map_merge(pair[1], merge_map)

            if state_i == state_j:
                continue
            
            # merge pair
            new_automaton, merges, accepting_and_rejecting = merge_states(automaton, state_i, state_j)

            # prepare output
            index_i = str(i).zfill(3)
            index_j = str(j).zfill(3)

            word_i = pair[0]
            word_j = pair[1]

            save_file_prefix = path + index_i + '-' + index_j
            reference = '(' + index_i + '-' + index_j + ')'

            print_array = ['ROOT MERGE ' + state_i + ' (' + word_i + ')' + ' & ' + state_j + ' (' + word_j + ') ' + reference,
                           '\n',
                           'MERGES THAT FOLLOWED:',
                           str(merges),
                           '\n',
                           'TO RECEIVE THIS SET OF STATES:',
                           str(new_automaton.states)]

            # check if negative sample is accepted
            neg_sample_accepted = None
            for neg_sample in neg_samples:

                result = new_automaton.run(neg_sample, verbose=False) if not is_bdfa else new_automaton.run_as_bdfa(neg_sample, verbose=False)
                if result:
                    neg_sample_accepted = neg_sample
                    break

            # merge was invalid, save violating samples
            if neg_sample_accepted is not None:

                print_array[0] = '>> [NO]: ' + print_array[0]
                print_array = print_array + ['\n', 'MERGES NOT EXECUTED BECAUSE THE FOLLOWING NEGATIVE SAMPLES WERE ACCEPTED:', str(neg_sample_accepted)]
                hp.save_to_text_file(print_array, save_file_prefix + '_not_merged.txt')

            elif len(accepting_and_rejecting) > 0:
                
                print_array[0] = '>> [NO]: ' + print_array[0]
                print_array = print_array + ['\n', 'MERGES NOT EXECUTED BECAUSE THE FOLLOWING STATES ARE ACCEPTING AND REJECTING:', str(accepting_and_rejecting)]
                hp.save_to_text_file(print_array, save_file_prefix + '_not_merged.txt')

            # merge was successful, document merge result 
            else:
                automaton = copy.deepcopy(new_automaton)

                print_array[0] = '>> [YES]: ' + print_array[0]
                hp.save_to_text_file(print_array, save_file_prefix + '_merged.txt')

                automaton.draw(path=path + index_i + '-' + index_j + '_automaton')
                
                # update merge map
                for merge in merges:
                    if merge not in merge_map:
                        merge_map.append(merge)

                merged = True
            j += 1
        if not merged:  break
        i += 1

    automaton.draw(include_sink=False, path=path + 'result', verbose=False)

    automaton.name = 'minimal'
    return automaton




def _summarize_dir(directory):
    """
    Read all .txt files in a directory in sorted order and concatenate their contents

    :param directory: path string to the directory

    :return: concatenated string of all .txt file contents
    """

    summary = ''
    for file in sorted(os.listdir(os.fsencode(directory))):
        filename = os.fsdecode(file)
        if filename.endswith(".txt"):
            with open(directory + filename, "r", encoding="utf-8") as f:
                summary += '\n-------------------------------\n\n' + f.read()
    return summary

def learn_dfa(alphabet, pos_samples, neg_samples, state_merging_algorithm, consistency_type: Literal['type_1', 'type_2'], name=''):
    """
    Learns a DFA based on positive and negative samples of a language, saves detailed output and rendered automaton steps

    :param alphabet: language alphabet
    :param pos_samples: list of words to accept
    :param neg_samples: list of words to reject
    :param state_merging_algorithm: used state merging algorithm
    :param consistency_type: type of consistency checks (type_1 is accepting/rejecting states, type_2 is running negative samples)
    :param name: name of language

    :return: learned DFA
    """

    # prepare output
    if name == '':  name = str(time.time())
    output_dir = "output/learn_dfa__" + name + '/'

    if os.path.isdir(output_dir):
        shutil.rmtree(output_dir)
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    os.chmod(output_dir,0o777)

    # save input info
    hp.save_to_text_file([
            'POSITIVE SAMPLES:', 
            str(pos_samples), 
            '\n'
            'NEGATIVE SAMPLES:', 
            str(neg_samples), 
            '\n\n'
            'STATE MERGING ALGORITHM:',
            state_merging_algorithm.__name__,
            '\n',
            'CONSISTENCY CHECKS:',
            'run negative samples after merge' if consistency_type == 'type_2' else 'disallow merging accepting and rejecting states'],
        output_dir + '_input.txt'
    )

    # distinguish consistency types by passing the negative samples to different functions
    negative_samples_pta, negative_samples_merging = [], []
    if consistency_type == 'type_1':
        negative_samples_pta, negative_samples_merging = neg_samples, []
    if consistency_type == 'type_2':
        negative_samples_pta, negative_samples_merging = [], neg_samples

    # learn dfa
    prefix_automaton = make_prefix_automaton(positive_samples=pos_samples, alphabet=alphabet, negative_samples=negative_samples_pta)
    learned_dfa = state_merging_algorithm(automaton=prefix_automaton, neg_samples=negative_samples_merging, path=output_dir)

    hp.save_to_text_file([_summarize_dir(output_dir)], output_dir + '_summary.txt')

    print('LEARNING DFA SAVED UNDER ' + output_dir)
    return learned_dfa

def learn_monoid(alphabet, pos_samples, neg_samples, state_merging_algorithm, consistency_type: Literal['type_1', 'type_2'], name=''):
    """
    Learns a monoid based on positive and negative samples of a language, saves detailed output and rendered automaton steps

    :param alphabet: language alphabet
    :param pos_samples: list of words to accept
    :param neg_samples: list of words to reject
    :param state_merging_algorithm: used state merging algorithm
    :param consistency_type: type of consistency checks (type_1 is accepting/rejecting states, type_2 is running negative samples)
    :param name: name of language

    :return: minimal monoid
    """

    # prepare output
    if name == '':  name = str(time.time())
    output_dir = "output/learn_monoid__" + name + '/'

    if os.path.isdir(output_dir):
        shutil.rmtree(output_dir)
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    os.chmod(output_dir,0o777)
    
    # save input info
    hp.save_to_text_file([
            'POSITIVE SAMPLES:', 
            str(pos_samples), 
            '\n'
            'NEGATIVE SAMPLES:', 
            str(neg_samples), 
            '\n\n'
            'STATE MERGING ALGORITHM:',
            state_merging_algorithm.__name__,
            '\n',
            'CONSISTENCY CHECKS:',
            'run negative samples after merge' if consistency_type == 'type_2' else 'disallow merging accepting and rejecting states'],
        output_dir + '_input.txt'
    )

    # distinguish consistency types by passing the negative samples to different functions
    negative_samples_pta, negative_samples_merging = [], []
    if consistency_type == 'type_1':
        negative_samples_pta, negative_samples_merging = neg_samples, []
    if consistency_type == 'type_2':
        negative_samples_pta, negative_samples_merging = [], neg_samples

    # learn monoid
    bdfa = make_infix_automaton(positive_samples=pos_samples, alphabet=alphabet, negative_samples=negative_samples_pta)
    learned_monoid = state_merging_algorithm(automaton=bdfa, neg_samples=negative_samples_merging, path=output_dir, is_bdfa=True)
    cayley = get_right_cayley_graph_from_bdfa(learned_monoid)
    cayley.draw(include_sink=False, path=output_dir + 'result_cayley', verbose=False)

    hp.save_to_text_file([_summarize_dir(output_dir)], output_dir + '_summary.txt')

    print('LEARNING MONOID SAVED UNDER ' + output_dir)
    return learned_monoid


def compare_learning(alphabet, pos_samples, neg_samples, state_merging_algorithm_dfa, consistency_type_dfa: Literal['type_1', 'type_2'], state_merging_algorithm_monoid, consistency_type_monoid: Literal['type_1', 'type_2'], name=''):
    """
    Learns a DFA and a monoid based on positive and negative samples of a language,
    saves detailed output and rendered automaton steps of both versions

    :param alphabet: language alphabet
    :param pos_samples: list of words to accept
    :param neg_samples: list of words to reject
    :param state_merging_algorithm_dfa: state merging algorithm to use for DFA learning
    :param consistency_type_dfa: type of consistency checks for DFA learning (type_1 is accepting/rejecting states, type_2 is running negative samples)
    :param state_merging_algorithm_monoid: state merging algorithm to use for monoid learning
    :param consistency_type_monoid: type of consistency checks for monoid learning (type_1 is accepting/rejecting states, type_2 is running negative samples)
    :param name: name of language

    """

    # prepare output
    if name == '':  name = str(time.time())
    output_dir = "output/learning_comparison__" + name + '/'
    
    if os.path.isdir(output_dir):
        shutil.rmtree(output_dir)
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    os.chmod(output_dir,0o777)

    # save input info
    hp.save_to_text_file([
            'POSITIVE SAMPLES:', 
            str(pos_samples), 
            '\n'
            'NEGATIVE SAMPLES:', 
            str(neg_samples), 
            '\n\n',
            'STATE MERGING ALGORITHM (DFA):',
            state_merging_algorithm_dfa.__name__,
            '\n',
            'CONSISTENCY CHECKS (DFA):',
            'run negative samples after merge' if consistency_type_dfa == 'type_2' else 'disallow merging accepting and rejecting states',
            '\n\n',
            'STATE MERGING ALGORITHM (MONOID):',
            state_merging_algorithm_monoid.__name__,
            '\n',
            'CONSISTENCY CHECKS (MONOID):',
            'run negative samples after merge' if consistency_type_monoid == 'type_2' else 'disallow merging accepting and rejecting states'],
        output_dir + '_input.txt'
    )

    # prepare dfa output
    subdir_dfa = 'dfa/'

    # distinguish consistency types by passing the negative samples to different functions
    negative_samples_pta, negative_samples_merging = [], []
    if consistency_type_dfa == 'type_1':
        negative_samples_pta, negative_samples_merging = neg_samples, []
    if consistency_type_dfa == 'type_2':
        negative_samples_pta, negative_samples_merging = [], neg_samples

    # learn dfa
    prefix_automaton = make_prefix_automaton(positive_samples=pos_samples, alphabet=alphabet, negative_samples=negative_samples_pta)
    learned_dfa = state_merging_algorithm_dfa(automaton=prefix_automaton, neg_samples=negative_samples_merging, path=output_dir + subdir_dfa)

    hp.save_to_text_file([_summarize_dir(output_dir + subdir_dfa)], output_dir + subdir_dfa + '_summary.txt')

    # prepare monoid output
    subdir_monoid = 'monoid/'

    # distinguish consistency types by passing the negative samples to different functions
    negative_samples_pta, negative_samples_merging = [], []
    if consistency_type_monoid == 'type_1':
        negative_samples_pta, negative_samples_merging = neg_samples, []
    if consistency_type_monoid == 'type_2':
        negative_samples_pta, negative_samples_merging = [], neg_samples

    # learn monoid
    bdfa = make_infix_automaton(positive_samples=pos_samples, alphabet=alphabet, negative_samples=negative_samples_pta)
    learned_monoid = state_merging_algorithm_monoid(automaton=bdfa, neg_samples=negative_samples_merging, path=output_dir + subdir_monoid, is_bdfa=True)
    right_cayley = get_right_cayley_graph_from_bdfa(learned_monoid)
    right_cayley.draw(include_sink=False, path=output_dir + subdir_monoid + 'result_right_cayley', verbose=False)
    left_cayley = get_left_cayley_graph_from_bdfa(learned_monoid)
    left_cayley.draw(include_sink=False, path=output_dir + subdir_monoid + 'result_left_cayley', verbose=False)

    inconsistent_words, verdict = learned_monoid.is_bdfa_consistent()
    consistency_note = 'BDFA CONSISTENCY: ' + ('COMPLETE TRUE' if verdict == 2 else ('PARTIAL TRUE' if verdict == 1 else 'FALSE')) +'\n \n ' + (', '.join(inconsistent_words) + '\n \n  are inconsistent' if verdict != 2 else '')

    hp.save_to_text_file([_summarize_dir(output_dir + subdir_monoid)], output_dir + subdir_monoid + '_summary.txt')

    # move rendered steps for both procedures to parent directory
    directory = os.fsencode(output_dir + subdir_dfa)
    for file in sorted(os.listdir(directory)):
        filename = os.fsdecode(file)
        if filename.endswith(".png"):
            shutil.copy(output_dir + subdir_dfa + filename, output_dir + 'dfa_' + filename)

    directory = os.fsencode(output_dir + subdir_monoid)
    for file in sorted(os.listdir(directory)):
        filename = os.fsdecode(file)
        if filename.endswith(".png"):
            shutil.copy(output_dir + subdir_monoid + filename, output_dir + 'monoid_' + filename)

    # generate summary pdf with input as well as dfa and monoid output
    hp.combine_to_pdf(
        text_path=output_dir + '_input.txt',
        dfa_image_path=output_dir + 'dfa_result.png',
        monoid_image_path=output_dir + 'monoid_result.png',
        right_cayley_image_path=output_dir + 'monoid_result_right_cayley.png',
        left_cayley_image_path=output_dir + 'monoid_result_left_cayley.png',
        output_pdf_path=output_dir + '__summary_pdf.pdf',
        consistency_note=consistency_note
    )

    print('LEARNING COMPARISON SAVED UNDER ' + output_dir)

def rpni_sample_transfer_from_dfa_to_monoid(alphabet, monoid_automaton, consistency_type: Literal['type_1', 'type_2'], name=''):
    """
    Generates RPNI complete samples for the given BDFA, maps those to monoid samples, then compares DFA learning with DFA samples
    and monoid learning with mapped samples.

    :param alphabet: language alphabet
    :param monoid_automaton: BDFA for L
    :param consistency_type: type of consistency checks for learning (type_1 is accepting/rejecting states, type_2 is running negative samples)
    :param name: name of language
    """

    complete_alphabet = hp.get_lr_alphabet(alphabet)

    # prepare output
    if name == '':  name = str(time.time())
    output_dir = "output/rpni_sample_transfer__" + name + '/'

    if os.path.isdir(output_dir):
        shutil.rmtree(output_dir)
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    os.chmod(output_dir,0o777)

    subdir_dfa = 'dfa/'
    subdir_monoid = 'monoid/'

    # draw minimal monoid
    monoid_automaton.draw(include_sink=True, path=output_dir + 'source_automaton', verbose=False)

    # get rpni complete samples for monoid
    cover_sink = consistency_type == 'type_1'
    pos_samples_dfa, neg_samples_dfa = compute_rpni_complete_samples_for_dfa(monoid_automaton, cover_sink=cover_sink, has_lr_alphabet=True)

    # learn dfa
    neg_samples_PTA, neg_samples_merge = [], neg_samples_dfa
    if consistency_type == 'type_1':
        neg_samples_PTA, neg_samples_merge = neg_samples_dfa, []

    prefix_automaton = make_prefix_automaton(positive_samples=pos_samples_dfa, alphabet=complete_alphabet, negative_samples=neg_samples_PTA)
    learned_dfa = merge_with_rpni_order(automaton=prefix_automaton, neg_samples=neg_samples_merge, path=output_dir + subdir_dfa, has_lr_alphabet=True)

    hp.save_to_text_file([_summarize_dir(output_dir + subdir_dfa)], output_dir + subdir_dfa + '_summary.txt')

    # transfer samples
    pos_samples_monoid, neg_samples_monoid = [], []
    for sample in set(pos_samples_dfa).union(set(neg_samples_dfa)):

        transformed_sample = hp.lr_word_to_normal(sample, complete_alphabet)

        if sample in pos_samples_dfa:
            pos_samples_monoid.append(transformed_sample)
        if sample in neg_samples_dfa:
            neg_samples_monoid.append(transformed_sample)

    pos_samples_monoid, neg_samples_monoid = list(set(pos_samples_monoid)), list(set(neg_samples_monoid))

    # save input info
    hp.save_to_text_file([
            'POSITIVE SAMPLES DFA:', 
            str(pos_samples_dfa), 
            '\n'
            'NEGATIVE SAMPLES DFA:', 
            str(neg_samples_dfa),
            '',
            'POSITIVE SAMPLES MONOID:', 
            str(pos_samples_monoid), 
            '\n'
            'NEGATIVE SAMPLES MONOID:', 
            str(neg_samples_monoid),
            '\n',  
            'STATE MERGING ALGORITHM:',
            'RPNI' + (' with sink samples' if consistency_type == 'type_1' else ''),
            '\n'
            'CONSISTENCY CHECKS:',
            ('run negative samples after merge' if consistency_type == 'type_2' else 'disallow merging accepting and rejecting states')], 
        output_dir + '_input.txt'
    )
    
    # learn monoid
    neg_samples_PTA_monoid, neg_samples_merge_monoid = [], neg_samples_monoid
    if consistency_type == 'type_1':
        neg_samples_PTA_monoid, neg_samples_merge_monoid = neg_samples_monoid, []

    bdfa = make_infix_automaton(positive_samples=pos_samples_monoid, alphabet=alphabet, negative_samples=neg_samples_PTA_monoid)
    minimal_monoid = merge_with_rpni_order(automaton=bdfa, neg_samples=neg_samples_merge_monoid, path=output_dir + 'monoid/', is_bdfa=True)
    right_cayley = get_right_cayley_graph_from_bdfa(minimal_monoid)
    right_cayley.draw(include_sink=False, path=output_dir + 'monoid/result_right_cayley', verbose=False)
    left_cayley = get_left_cayley_graph_from_bdfa(minimal_monoid)
    left_cayley.draw(include_sink=False, path=output_dir + 'monoid/result_left_cayley', verbose=False)

    hp.save_to_text_file([_summarize_dir(output_dir + subdir_monoid)], output_dir + subdir_monoid + '_summary.txt')

    # move rendered steps for both procedures to parent directory
    directory = os.fsencode(output_dir + subdir_dfa)
    for file in sorted(os.listdir(directory)):
        filename = os.fsdecode(file)
        if filename.endswith(".png"):
            shutil.copy(output_dir + subdir_dfa + filename, output_dir + 'dfa_' + filename)

    directory = os.fsencode(output_dir + subdir_monoid)
    for file in sorted(os.listdir(directory)):
        filename = os.fsdecode(file)
        if filename.endswith(".png"):
            shutil.copy(output_dir + subdir_monoid + filename, output_dir + 'monoid_' + filename)

    # generate summary pdf with input as well as dfa and monoid output
    hp.combine_to_pdf(
        text_path=output_dir + '_input.txt',
        dfa_image_path=output_dir + 'dfa_result.png',
        monoid_image_path=output_dir + 'monoid_result.png',
        right_cayley_image_path=output_dir + 'monoid_result_right_cayley.png',
        left_cayley_image_path=output_dir + 'monoid_result_left_cayley.png',
        output_pdf_path=output_dir + '__summary_pdf.pdf'
    )

    print('RPNI SAMPLE TRANSFER SAVED UNDER ' + output_dir)
