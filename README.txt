1)Tokenise Hindi corpus.
python indic_tokenizer.py --i  corpus.txt --o hindi_5lac_tokenised.txt --l hin
2)Run the spell checker (Give an input sentence, with the index of the word for which spell cheking has to be done) 
python BigramModelSpellCheck.py

The code returns a ranked list of word suggestions (with most probable word on the top)
