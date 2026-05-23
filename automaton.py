"""
This class models the behaviour of a deterministic automaton. 
It also supports BDFAs (both-sided DFAs) and assumes the existence of a sink state for missing transitions.
"""

# ---------------- IMPORT ----------------
from graphviz import Digraph
import copy
import helpers as hp

# ---------------- FUNCTIONS ----------------
class Automaton:

    def __init__(self, name='my_automaton'):
        """
        Create a new automaton, set minimal alphabet and initial + sink state

        :param self: automaton object
        :param name: automaton name
        """

        self.name = name
        self.alphabet = set()

        self.accepting = set()
        self.rejecting = set()

        self.initial = 'ε'
        self.sink = 'ρ'

        self.states = {self.initial, self.sink}
        self.transitions = set()

    
    def set_alphabet(self, alphabet):
        """
        Set alphabet, reset transitions

        :param self: automaton object
        :param alphabet: automaton alphabet
        """

        self.alphabet = alphabet
        self.transitions = set()

    def set_states(self, states):
        """
        Set states, reset transitions, pick random initial state

        :param self: automaton object
        :param states: set of automaton states
        """

        self.states = states
        self.transitions = set()

        self.initial = list(states)[0]

    def set_initial(self, state):
        """
        Set initial state 

        :param self: automaton object
        :param state: initial state
        """

        if state in self.states:
            self.initial = state

    def set_sink(self, state):
        """
        Set sink state

        :param self: automaton object
        :param state: sink state
        """

        if state in self.states:
            self.sink = state


    def add_state(self, state):
        """
        Add state

        :param self: automaton object
        :param state: state to add
        """

        if not state in self.states:
            self.states.add(state)

    def remove_state(self, state):
        """
        Remove state and all transitions including this state

        :param self: automaton object
        :param state: state to remove

        :return: set of removed transitions
        """

        removed_transitions = set()
        if state in self.states:

            # remove state
            self.states.remove(state)
            if state in self.accepting:
                self.accepting.remove(state)

            if state in self.rejecting:
                self.rejecting.remove(state)

            # find transitions with state and remove
            for transition in self.transitions:
                if transition[0] == state or transition[2] == state:
                    removed_transitions.add(transition)

            for transition in removed_transitions:
                self.transitions.remove(transition)

            # if removed state was initial, set new initial state
            if state == self.initial and len(self.states) > 0:
                self.initial = list(self.states)[0]
                
        return removed_transitions
    

    def add_transition(self, state1, letter, state2):
        """
        Add transition

        :param self: automaton object
        :param state1: source state of transition to add
        :param letter: transition letter to add
        :param state2: goal state of transition to add

        :return: if adding transition was successful
        """

        if not (state1 in self.states) or not (state2 in self.states) or not (letter in self.alphabet):
            return False
        
        else:
            transition = (state1, letter, state2)

            if not transition in self.transitions:
                self.transitions.add( (state1, letter, state2) )

            return True
        
    def remove_transition(self, state1, letter, state2):
        """
        Remove transition

        :param self: automaton object
        :param state1: source state of transition to remove
        :param letter: transition letter to remove
        :param state2: goal state of transition to remove
        """

        if (state1, letter, state2) in self.transitions:
            self.transitions.remove((state1, letter, state2))


    def add_accepting_state(self, state):
        """
        Add accepting state

        :param self: automaton object
        :param state: new accepting state

        :return: if adding state was successful
        """

        if not (state in self.states):
            return False
        
        else:
            if not state in self.accepting:
                self.accepting.add(state)
                return True
            
        return False
    
    def add_rejecting_state(self, state):
        """
        Add rejecting state

        :param self: automaton object
        :param state: new rejecting state

        :return: if adding state was successful
        """

        if not (state in self.states):
            return False
        
        else:
            if not state in self.rejecting:
                self.rejecting.add(state)
                return True
            
        return False

    def replace_state(self, replace, new):
        """
        Replace a state with a different state, transferring all transitions and acceptance flags

        :param self: automaton object
        :param replace: state to replace
        :param new: replacement state name
        """

        if not replace in self.states:
            return
        
        new_transitions = []
        for transition in self.transitions:
            if transition[0] == replace:
                new_transitions.append((new, transition[1], transition[2]))
            if transition[2] == replace:
                new_transitions.append((transition[0], transition[1], new))

        is_accepting = replace in self.accepting
        is_rejecting = replace in self.rejecting

        self.remove_state(replace)
        self.add_state(new)

        if is_accepting:
            self.add_accepting_state(new)
        if is_rejecting:
            self.add_rejecting_state(new)

        for transition in new_transitions:
            self.add_transition(transition[0], transition[1], transition[2])
    

    def step(self, previous_state, letter):
        """
        Compute step of automaton, using previous state and transition letter

        :param self: automaton object
        :param previous_state: state the step starts from
        :param letter: transition letter of step

        :return: next state after step
        """

        if not previous_state in self.states or not letter in self.alphabet:
            return None
        
        # find transition to apply
        for transition in self.transitions:
            if transition[0] == previous_state and transition[1] == letter:
                return transition[2]
            
        # otherwise sink
        return self.sink
  
    def _execute_run(self, word):
        """
        Execute a run on word and return the final state and run string

        :param self: automaton object
        :param word: string to run

        :return: (final_state, run_string)
        """

        current_state = self.initial
        run = str(self.initial)

        while True:
            current_letter, word = hp.get_next_letter(word, self.alphabet)
            if current_letter is None:
                break

            # find transition to apply
            transitioned = False
            for transition in self.transitions:
                if transition[0] == current_state and transition[1] == current_letter:
                    current_state = transition[2]
                    transitioned = True
                    break

            # otherwise sink
            if not transitioned:
                current_state = self.sink
                break

            run += ' -' + current_letter + '-> ' + str(current_state)

        return current_state, run

    def run(self, word, verbose=True):
        """
        Compute run of automaton on word

        :param self: automaton object
        :param word: string to compute automaton run on
        :param verbose: function will print step info if True (default: True)

        :return: if run is accepting
        """

        original_word = word
        current_state, run = self._execute_run(word)
        result = current_state in self.accepting

        if verbose:
            print(run)
            print('run on "' + original_word + '" is ' + ('ACCEPTING' if result else 'REJECTING'))
            print('---------------')

        return result

    def run_nfa(self, word, verbose=True):
        """
        Compute run of automaton on word with NFA semantics (any accepting path suffices).

        :param word: string to compute run on
        :param verbose: print result if True (default: True)

        :return: True if any execution path accepts the word
        """

        current_states = {self.initial}
        for letter in word:
            next_states = set()
            for state in current_states:
                successors = {t[2] for t in self.transitions if t[0] == state and t[1] == letter}
                next_states.update(successors if successors else {self.sink})
            current_states = next_states

        result = bool(current_states.intersection(self.accepting))

        if verbose:
            print('nfa run on "' + word + '" is ' + ('ACCEPTING' if result else 'REJECTING'))
            print('---------------')

        return result

    def run_and_return_state(self, word, verbose=True):
        """
        Compute run of automaton on word, return final state

        :param self: automaton object
        :param word: string to compute automaton run on
        :param verbose: function will print step info if True (default: True)

        :return: final state
        """

        original_word = word
        current_state, run = self._execute_run(word)
        result = current_state in self.accepting

        if verbose:
            print(run)
            print('run on "' + original_word + '" is ' + ('ACCEPTING' if result else 'REJECTING'))
            print('---------------')

        return current_state
    
    
    def _compute_lr_runs(self, word):
        """
        Compute all possible LR runs for each split point in the word.
        Each character can be the 'beginner' — its left context becomes [l]-transitions
        and its right context becomes [r]-transitions, interleaved in all valid orderings.

        :param self: automaton object
        :param word: normal word string

        :return: list of (possible_run, print_run_prefix) pairs, one per split point
        """

        all_runs = []

        for i in range(0, len(word)):
            beginner = word[i]
            left_transitions, right_transitions = [], []

            # split into left and right transitions as they are independent
            for j in reversed(range(0, i)):
                left_transitions.append(word[j] + '[l]')

            for j in range(i + 1, len(word)):
                right_transitions.append(word[j] + '[r]')

            # compute possible runs by finding all possible combinations of left and right transitions without
            # changing individual order of lists
            possible_runs = []
            if len(left_transitions) > 0 and len(right_transitions) > 0:
                possible_runs = hp.interleave(left_transitions, right_transitions)
            elif len(left_transitions) > 0:
                possible_runs = [left_transitions]
            elif len(right_transitions) > 0:
                possible_runs = [right_transitions]

            # add beginner letter as left and right transition
            possible_runs_with_beginner = []
            for run in possible_runs:
                possible_runs_with_beginner.append([beginner + '[l]'] + run)
                possible_runs_with_beginner.append([beginner + '[r]'] + run)

            if len(possible_runs) == 0:
                possible_runs_with_beginner = [[beginner + '[l]'], [beginner + '[r]']]

            all_runs.extend(possible_runs_with_beginner)

        return all_runs

    def _execute_lr_run(self, possible_run):
        """
        Execute a single LR run (list of letters) and return the final state and run string

        :param self: automaton object
        :param possible_run: ordered list of LR letters

        :return: (final_state, run_string)
        """

        current_state = self.initial
        print_run = str(self.initial)

        for letter in possible_run:

            # find transition to apply
            transitioned = False
            for transition in self.transitions:
                if transition[0] == current_state and transition[1] == letter:
                    current_state = transition[2]
                    transitioned = True
                    break

            # otherwise sink
            if not transitioned:
                current_state = self.sink
                break

            print_run += ' -' + letter + '-> ' + str(current_state)

        return current_state, print_run

    def run_as_bdfa(self, word, verbose=True):
        """
        Compute run of BDFA on word, minding left and right transitions and
        finding a possible run on the automaton, provided there is one

        :param self: automaton object
        :param word: string to compute automaton run on
        :param verbose: function will print step info if True (default: True)

        :return: if accepting run was found
        """

        # special case: empty word
        if word == '':
            return self.initial in self.accepting

        for possible_run in self._compute_lr_runs(word):
            current_state, print_run = self._execute_lr_run(possible_run)

            if current_state in self.accepting:
                if verbose:
                    print(print_run)
                    print('run on "' + word + '" is ACCEPTING')
                    print('---------------')
                return True

        if verbose: print('no accepting run on "' + word + '" found')
        return False

    def run_and_return_states_as_bdfa(self, word, verbose=True):
        """
        Compute all reachable non-sink states across every possible LR run on word

        :param self: automaton object
        :param word: string to compute automaton run on
        :param verbose: function will print step info if True (default: True)

        :return: set of reachable non-sink states; {sink} if none were reached
        """

        # special case: empty word
        if word == '':
            return set([self.initial])

        states = set()

        for possible_run in self._compute_lr_runs(word):
            current_state, print_run = self._execute_lr_run(possible_run)

            if current_state in self.accepting:
                if verbose:
                    print(print_run)
                    print('run on "' + word + '" is ACCEPTING')
                    print('---------------')

            if current_state != self.sink:
                states.add(current_state)

        if len(states) == 0:
            if verbose:
                print('no accepting run on "' + word + '" found')
            return set([self.sink])
        else:
            return states
    
    def run_and_return_state_as_bdfa(self, word, verbose=True):
        """
        Compute LR run and return the unique final state. Raises if the result is not unique,
        which would indicate the automaton is not a syntactic monoid.

        :param self: automaton object
        :param word: string to compute automaton run on
        :param verbose: function will print step info if True (default: True)

        :return: unique final state
        """

        result = self.run_and_return_states_as_bdfa(word, verbose=verbose)
        if len(result) == 1:    return list(result)[0]
        else:   raise ValueError('The input was expected to be a syntactic monoid. Input word was "' + word + '", computed final states were ' + str(result))

    def is_bdfa_consistent(self, max_word_length=None):
        """
        Check if the BDFA is consistent: for every normal word, all LR representations of
        that word must reach the same state when run on the automaton.

        :param self: automaton object
        :param max_word_length: maximum normal word length to test (default: number of states)

        :return: (list of inconsistent words with their accepting states, verdict 0/1/2)
        """

        normal_alphabet = hp.get_normal_alphabet_from_lr(self.alphabet)
        if max_word_length is None:
            max_word_length = len(self.states)

        inconsistent_words = []
        for length in range(0, max_word_length + 1):
            for word in hp.words_of_length_x(normal_alphabet, length):

                final_states = set()
                for lr_word in hp.normal_word_to_lr(word):
                    final_state, _ = self._execute_run(lr_word)
                    final_states.add(final_state)

                if len(final_states) > 1:
                    inconsistent_word = ((word if word != '' else 'ε'), final_states)
                    inconsistent_words.append(inconsistent_word)

        partial_consistent = True
        for inconsistent_word in inconsistent_words:
            if len(inconsistent_word[1]) > 2 or self.sink not in inconsistent_word[1]:
                partial_consistent = False
                break

        inconsistent_words_str = []
        for inconsistent_word in inconsistent_words:
            inconsistent_words_str.append(inconsistent_word[0] + ' ' + str(inconsistent_word[1]))
                
        verdict = 2 if len(inconsistent_words) == 0 else (1 if partial_consistent else 0)
        return inconsistent_words_str, verdict

    def print(self):
        """
        Print automaton summary of attributes

        :param self: automaton object
        """

        print('ALPHABET:')
        print(", ".join(self.alphabet))
        print('---------------')

        print('STATES:')
        print(", ".join(self.states))
        print('---------------')

        print('INITIAL: ') 
        print(self.initial)
        print('---------------')

        print('ACCEPTING:')
        print(", ".join(self.accepting))
        print('---------------')

        print('REJECTING:')
        print(", ".join(self.rejecting))
        print('---------------')

        print('TRANSITIONS:')

        print_transitions = ''
        for transition in self.transitions:
            print_transitions += ' ,  (' + transition[0] + ', ' + transition[1] + ', ' + transition[2] + ')'
        print_transitions = print_transitions[4:]

        print(print_transitions)
        print('---------------')

    def draw(self, include_sink=False, path='', verbose=False):
        """
        Render visual representation of automaton

        :param self: automaton object
        :param include_sink: draw sink state and relevant transitions if True (default: True)
        :param path: file path to save files under (default: "")
        :param verbose: print info when render saved if True (default: True)
        """

        g = Digraph(
            name='Automaton',
            format='png',
            graph_attr={
                'rankdir': 'LR',
                'splines': 'true',
                'nodesep': '0.4',
                'ranksep': '0.6'
            }
        )

        # initial state with dummy node to show indicator arrow
        g.node('', shape='none')
        g.node(self.initial)
        g.edge('', self.initial)

        # refine transitions (merge transitions with same direction but different letters)
        refined_transitions = copy.deepcopy(self.transitions)
        removed_transitions = set()
        for transition in self.transitions:
            if transition in removed_transitions:
                continue

            labels = [transition[1]]

            for other_letter in self.alphabet.difference({transition[1]}):
                if (transition[0], other_letter, transition[2]) in self.transitions:
                    labels.append(other_letter)
                    removed_transitions.add((transition[0], other_letter, transition[2])) 

            if len(labels) > 1:

                labels = list(labels)
                labels.sort(key=lambda t: hp.canonical_word_key(t, self.alphabet))

                removed_transitions.add(transition)
                refined_transitions.add((transition[0], ", ".join(labels), transition[2]))

        refined_transitions = refined_transitions.difference(removed_transitions)

        # accepting states
        for state in self.accepting:
            g.node(state, shape='doublecircle')

        for state in self.rejecting:
            g.node(state, shape='Mcircle')
        
        # all other states
        for state in self.states.difference(self.accepting.union(self.rejecting).union({self.initial, self.sink})):
            g.node(state)

        # transitions
        for transition in refined_transitions:
            g.edge(transition[0], transition[2], label=transition[1])

        # sink transitions
        if include_sink:
            g.node(self.sink)
            g.edge(self.sink, self.sink, label=", ".join(self.alphabet))

            for state in self.states.difference({self.sink}):

                letters = []
                for letter in self.alphabet:
                    next_state = self.step(state, letter)
                    if next_state == self.sink:
                        letters.append(letter)

                if len(letters) > 0:
                    g.edge(state, self.sink, label=", ".join(letters))

        # render
        if path == '':
            path = 'output/' + self.name

        g.render(path)
        if verbose: print('AUTOMATON RENDER SAVED UNDER ' + path)



