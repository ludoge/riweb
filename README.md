# riweb

A school project to implement various Information Retrieval techniques for two document collections : CACM and CS276.

## Collection.py

Run this script to create an index for either collection.
It can also print some data about the collection (answers to questions for the project).
Indices are created  block by block (1 for CACM, 10 for CS276) and are compressed using variable-byte encoding.

## BooleanRequest.py

Interactive script to make boolean queries using Polish (prefix) notation.

## VectorRequest.py

A script to make queries in plain text, that are compared to indexed documents via a cosine-ssimilarity measure.

## Evaluation.py

Interactive script to evaluate our vector request engine according to various criteria. Only supports CACM.
