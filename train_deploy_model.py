"""Compatibility entry point for InterviewIQ model training.

The old version of this file used Gensim Word2Vec. The final project no
longer depends on Gensim and uses train_interviewiq.py for the complete
embedding/fusion/MLP pipeline.
"""

from train_interviewiq import main

if __name__ == "__main__":
    main()
