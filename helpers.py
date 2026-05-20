"""
This module contains various helper functions for general and automaton operations
"""

# ---------------- IMPORT ----------------
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

# ---------------- FUNCTIONS ----------------

# >> recursive helpers

def interleave(array1, array2, i=0, j=0, prefix=None):
    """
    Recursively combines two array to one in every possible way without changing the original order of the arrays

    :param array1: array to combine
    :param array2: array to combine
    :param i: iterator for array1
    :param j: iterator for array2
    :param prefix: current combined array of recursive branch

    :return: combined array
    """

    if prefix is None:
        prefix = []

    results = []

    # both arrays are iterated to finish, save concatenated prefix
    if (i == len(array1) and j == len(array2)):
        #interleave_results.append(prefix)
        #return interleave_results
        return [prefix]

    # recursive step when advancing in array1
    if (i < len(array1)):
        new_prefix = prefix + [array1[i]]
        results = results + interleave(array1, array2, i=i+1, j=j, prefix=new_prefix)

    # recursive step when advancing in array2
    if (j < len(array2)):
        new_prefix = prefix + [array2[j]]
        results = results + interleave(array1, array2, i=i, j=j+1, prefix=new_prefix)

    return results

def words_of_length_x(alphabet, length, has_lr_alphabet=False, i=0, prefix=""):
    """
    Generate all words of a given length over the alphabet in canonical order

    :param alphabet: alphabet to use
    :param length: word length
    :param has_lr_alphabet: if alphabet contains LR letters (used for sorting)
    :param i: current depth in recursion
    :param prefix: current word prefix

    :return: list of all words of the given length in canonical order
    """

    if i == length:
        return [prefix]

    words = []
    for letter in alphabet:
        words += words_of_length_x(alphabet, length, has_lr_alphabet=has_lr_alphabet, i=i+1, prefix=prefix+letter)

    words.sort(key=lambda t: canonical_word_key(t, alphabet, is_lr=has_lr_alphabet))
    return words


# >> save helpers

def save_to_text_file(lines, path):
    """
    Writes array of string to text file after replacing certain special characters

    :param lines: string array to save
    :param path: file path to save the text file under
    """

    for i in range(0, len(lines)):
        lines[i] = lines[i].replace('ε', '\u03b5').replace('ρ', '\u03c1') + '\n'

    with open(path, "w", encoding="utf-8") as text_file:
        text_file.writelines(lines)

def combine_to_pdf(
    text_path: str,
    dfa_image_path: str,
    monoid_image_path: str,
    right_cayley_image_path: str,
    left_cayley_image_path: str,
    output_pdf_path: str,
    consistency_note: str = None,
    bdfa_language_note: str = None,
    right_cayley_language_note: str = None,
    left_cayley_language_note: str = None,
):
    """
    Creates a PDF containing:
    - text file content
    - label 'DFA:' + DFA image (scaled to page width)
    - label 'MONOID:' + monoid image + optional consistency note + optional language note
    - label 'RIGHT CAYLEY:' + right Cayley image + optional language note
    - label 'LEFT CAYLEY:' + left Cayley image + optional language note
    """

    def add_note(note):
        story.append(Spacer(1, 8))
        for line in note.split('\n'):
            story.append(Paragraph(line, styles["Normal"]))

    # read text file
    with open(text_path, "r", encoding="utf-8") as f:
        text_content = f.read()

    # setup document
    doc = SimpleDocTemplate(output_pdf_path, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # available width inside page margins
    available_width = doc.width

    # add text content
    for line in text_content.splitlines():
        story.append(Paragraph(line.replace(" ", "&nbsp;"), styles["Normal"]))
        story.append(Spacer(1, 6))

    # DFA
    story.append(Spacer(1, 12))
    story.append(Paragraph("<b>DFA:</b>", styles["Heading2"]))
    story.append(Spacer(1, 12))

    dfa_img = Image(dfa_image_path)
    dfa_scale = available_width / dfa_img.imageWidth
    dfa_img.drawWidth = available_width
    dfa_img.drawHeight = dfa_img.imageHeight * dfa_scale
    story.append(dfa_img)

    # MONOID
    story.append(Spacer(1, 24))
    story.append(Paragraph("<b>MONOID:</b>", styles["Heading2"]))
    story.append(Spacer(1, 12))

    monoid_img = Image(monoid_image_path)
    monoid_scale = available_width / monoid_img.imageWidth
    monoid_img.drawWidth = available_width
    monoid_img.drawHeight = monoid_img.imageHeight * monoid_scale
    story.append(monoid_img)

    if consistency_note is not None:    add_note(consistency_note)
    if bdfa_language_note is not None:  add_note(bdfa_language_note)

    # RIGHT CAYLEY
    story.append(Spacer(1, 24))
    story.append(Paragraph("<b>RIGHT CAYLEY:</b>", styles["Heading2"]))
    story.append(Spacer(1, 12))

    right_cayley_img = Image(right_cayley_image_path)
    right_cayley_scale = available_width / right_cayley_img.imageWidth
    right_cayley_img.drawWidth = available_width
    right_cayley_img.drawHeight = right_cayley_img.imageHeight * right_cayley_scale
    story.append(right_cayley_img)

    if right_cayley_language_note is not None:  add_note(right_cayley_language_note)

    # LEFT CAYLEY
    story.append(Spacer(1, 24))
    story.append(Paragraph("<b>LEFT CAYLEY:</b>", styles["Heading2"]))
    story.append(Spacer(1, 12))

    left_cayley_img = Image(left_cayley_image_path)
    left_cayley_scale = available_width / left_cayley_img.imageWidth
    left_cayley_img.drawWidth = available_width
    left_cayley_img.drawHeight = left_cayley_img.imageHeight * left_cayley_scale
    story.append(left_cayley_img)

    if left_cayley_language_note is not None:   add_note(left_cayley_language_note)

    # build pdf
    doc.build(story)


# >> state merge helpers

def map_merge(state, merge_map):
    """
    Maps state to equivalent state after merges using a merge map of previous merges

    :param state: state to map
    :param merge_map: set of merge triples (first merged state, second merged state, result merged state)

    :return: mapped state
    """

    mapped = state
    while(True):

        # find mapping in merge and apply
        mapping_found = False
        for triple in merge_map:
            if triple[0] == mapped or triple[1] == mapped:
                mapped = triple[2]
                mapping_found = True
                
        # if no mapping found, we are finished
        if not mapping_found:
            break
        
    return mapped

def remove_merges(merges, state):
    """
    From a set of tuples denoting the intended merging of two states, remove all merges including a specific state

    :param merges: set of merge tuples (state to merge, state to merge)
    :param state: state to search for in merge tuples

    :return: modified merge set, set of removed merges
    """

    removed = set()
    for tuple in merges:
        if (tuple[0] == state or tuple[1] == state):
            removed.add(tuple)

    merges = merges.difference(removed)
    return merges, removed

def compute_merge_name(state1, state2, alphabet):
    """
    Compute merge name of two states using canonical order

    :param state1: state to merge
    :param state2: state to merge
    :param alphabet: alphabet used for canonical ordering

    :return: merged state name
    """


    words = state1.split('_')
    words += state2.split('_')

    words.sort(key=lambda t: canonical_word_key(t, alphabet))
    return '_'.join(words)


# >> alphabet helpers

def canonical_word_key(word, alphabet, is_lr=False):
    """
    Compute a sort key for canonical ordering: by length first, then lexicographically.
    Empty word ε is always smallest; sink ρ is always largest.
    For LR words, secondary ordering uses the L/R transition pattern.

    :param word: word to compute key for
    :param alphabet: alphabet (used to parse LR letters)
    :param is_lr: if word is over an LR alphabet

    :return: tuple used as sort key
    """

    if word == 'ε':
        return (-2, (), ())
    if word == 'ρ':
        return (10**9, (), ())

    if not is_lr:
        return (len(word), word, 1)

    symbols = []
    current_word = word
    while True:
        current_letter, current_word = get_next_letter(current_word, alphabet)
        if current_letter is None:
            break
        symbols.append(current_letter)

    rl_pattern = tuple(0 if s.endswith('[r]') else 1 for s in symbols)
    base_letters = tuple(s[:-3] for s in symbols)  # strips [l]/[r]

    return (len(symbols), rl_pattern, base_letters)

def get_next_letter(word, alphabet):
    """
    Consume the next letter from a word by matching the start of the word against the alphabet.
    Handles multi-character letters (e.g. LR letters like "a[l]").

    :param word: remaining word string
    :param alphabet: set of valid letters

    :return: (letter, remainder) — letter is None if no match found
    """

    for letter in alphabet:
        if word.startswith(letter):
            return letter, word[len(letter):len(word)]
        
    return None, word


def lr_word_to_normal(word, alphabet):
    """
    Convert an LR word (sequence of a[l]/a[r] letters) back to a normal word.
    Left letters are prepended, right letters are appended.

    :param word: LR word string
    :param alphabet: LR alphabet

    :return: normal word string
    """

    transformed_word = ''
    while True:
        current_letter, word = get_next_letter(word, alphabet)
        if current_letter is None:
            break
        
        if current_letter.endswith('[r]'):
            transformed_word = transformed_word + current_letter.replace('[r]', '')
        if current_letter.endswith('[l]'):
            transformed_word = current_letter.replace('[l]', '') + transformed_word

    return transformed_word
        
def normal_word_to_lr(word):
    """
    Convert a normal word to all possible LR representations.
    For each split point, the left part becomes [l]-transitions (reversed) and
    the right part becomes [r]-transitions, interleaved in all valid orderings.

    :param word: normal word string

    :return: set of all LR word strings that represent the input word
    """

    all_runs = []
    for i in range(0, len(word)+1):
        left_transitions, right_transitions = [], []

        # split into left and right transitions as they are independent
        for j in reversed(range(0, i)):
            left_transitions.append(word[j] + '[l]')
        
        for j in range(i, len(word)):
            right_transitions.append(word[j] + '[r]')

        # compute possible runs by finding all possible combinations of left and right transitions without
        # changing individual order of lists
        runs = interleave(left_transitions, right_transitions)
        all_runs = all_runs + runs

    all_words = set()
    for run in all_runs:

        lr_word = ''
        for el in run:
            lr_word = lr_word + el
        all_words.add(lr_word)

    return all_words

def get_lr_alphabet(alphabet):
    """
    Expand a normal alphabet to its LR version by adding [l] and [r] variants for each letter

    :param alphabet: normal alphabet

    :return: LR alphabet with a[l] and a[r] for each letter a
    """

    complete_alphabet = set()

    for letter in alphabet:
        complete_alphabet.add(letter + '[r]')
        complete_alphabet.add(letter + '[l]')

    return complete_alphabet

def get_normal_alphabet_from_lr(alphabet):
    """
    Recover the normal alphabet from an LR alphabet by stripping [l]/[r] suffixes

    :param alphabet: LR alphabet

    :return: normal alphabet
    """

    normal_alphabet = set()
    for letter in alphabet:
        normal_alphabet.add(letter.replace('[l]', '').replace('[r]', ''))

    return normal_alphabet