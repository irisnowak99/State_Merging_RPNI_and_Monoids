This project is a python implementation in the context of a bachelor thesis based on the paper:

"Learning Syntactic Monoids from Samples by extending known Algorithms for learning State Machines" by Simon Dieck and Sicco Verwer.

The project implements the classic RPNI merging algorithm for learning a DFA recognizing regular languages defined by positive and negative samples. Furthermore the RPNI algorithm is modified to work with a BDFA (both-sided DFA) so a monoid recognizing the language is obtained instead, as outlined by the paper.

## Dependencies

```
pip install -r requirements.txt
```

Requires [Graphviz](https://graphviz.org/download/) to be installed on the system as well.

## Usage

Run `main.py` to execute the examples. Output (automaton renders, step-by-step merge logs, summary PDFs) is written to `output/`.
