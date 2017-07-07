# -*- coding: utf-8 -*-
"""
Created on Thu Nov 26 18:47:02 2015

@author: nausheenfatma
"""

from indic_tokenizer import tokenizer

class BigramModelSpellCheck:
	def __init__(self):
		self.raw_file="corpus_tokenised.txt" # "test_tokenised"   file containing tokenised words,sentence seperator='$$$'
		self.bigrams={}
		self.unigrams={}
  
  
	def make_unigrams(self):
		f=open(self.raw_file,"r")
		for line in f:
			line=line.rstrip()
			if line in self.unigrams:
				self.unigrams[line]=self.unigrams[line]+1				
			else :
				self.unigrams[line]=1


	def make_bigrams(self):
		f=open(self.raw_file,"r")
		k_minus_1_word="$$$"
		while True:	
			line=f.readline()
			if not line: break 
			line=line.rstrip()
			k_word=line
			bigram=k_minus_1_word+"_"+k_word
			if not line=="$$$":
				if bigram in self.bigrams:
					self.bigrams[bigram]=self.bigrams[bigram]+1 #increase count by 1
				else :
					self.bigrams[bigram]=1	#initialise count=1

			k_minus_1_word=line;			#for next bigram,update k-1

	def save_grams(self,filename,gram_dict):
		f=open(filename,"w")
		for gram in gram_dict:
			f.write(gram+"\t"+str(gram_dict[gram]))
			#f.write("")
			f.write("\n")

	def find_bigram_likelihood(self,a_comma_b):
		no_a_and_b=self.bigrams[a_comma_b]
		b=a_comma_b.split("_")[1]
		no_b=self.unigrams[b]
		bigram_prob=no_a_and_b/float(no_b)
		print bigram_prob

	def sentence_tokenizer(self,line):
		tzr = tokenizer()
		line = line.decode('utf-8')
		line = tzr.normalize(line)
		line = tzr.tokenize(line)
		return line


	def sentence_likelihood(self,line): #line here represent string with \n as separator
        #finding tokens/unigrams
	    #line=self.sentence_tokenizer(line)
	    #finding bigrams below   
	    tokens = line.split("\n")
	    prev_token=tokens[0].encode("utf-8")
	    bigrams=[]
	    sentence_likelihood=1
	    for index in range(1,len(tokens)):
	    	next_token=tokens[index].encode('utf-8')
	    	bigram=prev_token+"_"+next_token
	    	bigrams.append(bigram)
	    	print bigram
	    	prev_token=next_token
        #finding bigram likelihood of the sentence
		
	    for bigram in bigrams:
	    	n_bigram=0
	    	if bigram in self.bigrams:
				n_bigram=self.bigrams[bigram]
			#print n_bigram
	    	first_word=bigram.split("_")[0]
	    	n_first_word=0
	    	if n_first_word in self.unigrams:
				n_first_word=self.unigrams[first_word]
	    	V=len(self.unigrams)
	    	bigram_likelihood=(n_bigram+1)/float(n_first_word+V) #a simple add 1 smoothing
	    	sentence_likelihood=sentence_likelihood*bigram_likelihood
			
	    print "sentence_likelihood",sentence_likelihood
	    return sentence_likelihood


	def create_edited_words(self,word): #for hindi
	    CHARACTERS_TO_REPLACE=['ी','ि','ु','े','ै','ो','ौ','़','्','ं','ँ','आ','अ','ए','ऐ','ओ','औ','इ','ई' ,'ी','ा','ू']
	    SOFT_VOWELS=['ि','ु','े','़','्','ं','ँ'] #observation is insertion and deletion edits can have only these characters

		#splitting the word into all possible number of sequential parts 
	    splits=[(word[:3*i], word[3*i:]) for i in range((len(word))/3 + 1)]		#hindi character has length=3
	    
		#deletes  of matra below
	    deletes=[]

	    for a,b in splits:
	    	#print a,b
	    	#print b[0:3]
	    	#print b[3:]
	    	if b[0:3] in SOFT_VOWELS:
	    		edited_word=a+b[3:]
	    		#print "edited",edited_word
	    		deletes.append(edited_word)


        # replace of matra below
	    replaces=[]
	    for a,b in splits:     
        	if b[0:3] in CHARACTERS_TO_REPLACE:
        		for character in CHARACTERS_TO_REPLACE:
        			if character !=b[0:3]:
        				edited_word=a+character+b[3:]
        				replaces.append(edited_word)
        				#print edited_word
        # insert of matra below
	    inserts=[]
 	    for a,b in splits: 
 	    	#print "here",a[-3:]
        	if b[0:3] not in CHARACTERS_TO_REPLACE and a[-3:] not in  CHARACTERS_TO_REPLACE: 
        		for character in SOFT_VOWELS:       		
        			edited_word=a+character+b
        			inserts.append(edited_word) 
 	    edit_set=inserts+deletes+replaces+[word]
           
 	    return set(edit_set)

	def edits2(self,word):
		return set(e2 for e1 in self.create_edited_words(word) for e2 in self.create_edited_words(e1))
			
	def prune_out_of_vocab_words(self,edit_set):
		candidate_words=[]
		for e1 in edit_set:
			if e1 in self.unigrams:
				candidate_words.append(e1)	
		return candidate_words

	def find_max_edit_likelihood(self,sentence,word_offset):
		sentence=self.sentence_tokenizer(sentence)
		tokens=sentence.split("\n")
		temp=tokens[:]
		max_prob=self.sentence_likelihood(sentence)		#initialise max probability to the original word
		if len(tokens) > word_offset :
			word_to_edit=tokens[word_offset-1]
			word_to_edit= word_to_edit.encode("utf-8")
			print word_to_edit
			candidate_words=self.prune_out_of_vocab_words(self.edits2(word_to_edit))
			print len(candidate_words)
   			word_with_max_prob=word_to_edit
                
			for word in candidate_words:
				temp[word_offset-1]=word.decode("utf-8")
				new_sentence="\n".join(temp)
				prob=self.sentence_likelihood(new_sentence)
				print "word="+word+"prob="+str(prob)
				if max_prob < prob:
					max_prob=prob
					word_with_max_prob=word
				#print new_sentence.encode("utf-8")
			print "word with max prob"+word_with_max_prob+" has max prob of "+str(max_prob)





def main():
	bm=BigramModelSpellCheck()
	bm.make_bigrams()
	bm.save_grams("bigrams.txt",bm.bigrams)		#optional step,just for viewing the bigrams
	bm.make_unigrams()
	bm.save_grams("unigrams.txt",bm.unigrams)	#optional step,just for viewing the unigrams
	# bm.find_bigram_likelihood("तीन_फीसदी")
 

	#commented 3 lines of code below on how to find sentence likelihood
	#line="हथियारों की तादाद के बारे में यकीन से कछ नहीं कहा जा सकता"
	#line=bm.sentence_tokenizer(line)
	#bm.sentence_likelihood(line)
 
	
	#To find the maximum likelihood of a sentence by editing the word at the give the offset. 	
	#bm.find_max_edit_likelihood("दो मोटर साइकिल स्वारों ने चालीस बर्स के डॉक्टर राशिद महदी को फायरिंग कर के हलाक कर दिया",4)
	#bm.find_max_edit_likelihood("जो भी हल निकालआ जाए",4)
	bm.find_max_edit_likelihood("ईश्वर्य राय और सलमान खान ने हिदायत कार संजय भंसाली की मशहूर फिल्म हम दल दे चुके सनम में साथ काम किया था",1) 
 	#bm.find_max_edit_likelihood("चिनांचा सेंसर बोर्ड के अरकॉन जब शिकायत् सुनने के बाद पड़ताल कर लिए हॉल में पहुँचते",7)



if __name__ == '__main__':
	main()
