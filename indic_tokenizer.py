#!/usr/bin/env python
# -*- coding=utf-8 -*-

import re
import sys
import os.path
import argparse

ENCHANT = True

try:
    import enchant
except ImportError:
    ENCHANT = False

class tokenizer():
    def __init__(self, lang='hin'):
        self.lang = lang
        self.WORD_JOINER=u'\u2060'
        self.SOFT_HYPHEN=u'\u00AD'
        self.BYTE_ORDER_MARK=u'\uFEFF'
        self.BYTE_ORDER_MARK_2=u'\uFFFE'
        self.NO_BREAK_SPACE=u'\u00A0'
        self.ZERO_WIDTH_SPACE=u'\u200B'
        self.ZERO_WIDTH_JOINER=u'\u200D'
        self.ZERO_WIDTH_NON_JOINER=u'\u200C'

        file_path = os.path.abspath(__file__).rpartition('/')[0]
        if ENCHANT:
            self.en_dict = enchant.Dict('en_US')

        self.ben = lang in ["ben", "asm"]
        self.dev = lang in ["hin", "mar", "nep", "bod", "kok"]
	self.urd = lang == 'urd'
	self.tam = lang == 'tam'
	self.tel = lang == 'tel'
	self.mal = lang == 'mal'
	self.kan = lang == 'kan'
	self.guj = lang == 'guj'
	self.pan = lang == 'pan'
	self.ori = lang == 'ori'

        #load nonbreaking prefixes from file
	with open('%s/NONBREAKING_PREFIXES' %file_path) as fp:
	    self.NBP = dict()
	    for line in fp:
		if not line.startswith('#'):
		    if '#NUMERIC_ONLY#' in line:
			self.NBP[line.replace('#NUMERIC_ONLY#', '').split()[0]] = 2
		    else:
			self.NBP[line.strip()] = 1

    def normalize(self,text):
        """
        Performs some common normalization, which includes: 
            - Byte order mark, word joiner, etc. removal 
            - ZERO_WIDTH_NON_JOINER and ZERO_WIDTH_JOINER removal 
            - ZERO_WIDTH_SPACE and NO_BREAK_SPACE replaced by spaces 
        """

        text=text.replace(self.BYTE_ORDER_MARK,'')
        text=text.replace(self.BYTE_ORDER_MARK_2,'')
        text=text.replace(self.WORD_JOINER,'')
        text=text.replace(self.SOFT_HYPHEN,'')

        text=text.replace(self.ZERO_WIDTH_SPACE,' ') 
        text=text.replace(self.NO_BREAK_SPACE,' ')

        text=text.replace(self.ZERO_WIDTH_NON_JOINER, '')
        text=text.replace(self.ZERO_WIDTH_JOINER,'')

        return text

    def tokenize(self, text):
        #text = ' %s ' %' '.join(text.split())
        text = ' %s ' %' '.join(text.split())
        # remove junk characters
        text = re.sub('[\x00-\x1f]', '', text)
        # seperate out on Latin-1 supplementary characters
        text = re.sub(u'([\xa1-\xbf\xd7\xf7])', r' \1 ', text)        
        # seperate out on general unicode punctituations except "’"
        text = re.sub(u'([\u2000-\u2018\u201a-\u206f])', r' \1 ', text)        
        # seperate out on unicode mathematical operators
        text = re.sub(u'([\u2200-\u22ff])', r' \1 ', text)        
        # seperate out on unicode fractions
        text = re.sub(u'([\u2150-\u2160])', r' \1 ', text)        
        # seperate out on unicode superscripts and subscripts
        text = re.sub(u'([\u2070-\u209f])', r' \1 ', text)        
        # seperate out on unicode currency symbols
        text = re.sub(u'([\u20a0-\u20cf])', r' \1 ', text)        
        # seperate out all "other" ASCII special characters
        text = re.sub(u"([^\u0080-\U0010ffffa-zA-Z0-9\s\.'`,-])", r' \1 ', text)        

        #keep multiple dots together
        text = re.sub(r'(\.\.+)([^\.])', lambda m: r' %sMULTI %s' %('DOT'*len(m.group(1)), m.group(2)), text)
	if self.urd:
	    #keep multiple dots (urdu-dots) together
	    text = re.sub(u'(\u06d4\u06d4+)([^\u06d4])', lambda m: r' %sMULTI %s' %('DOTU'*len(m.group(1)), m.group(2)), text)
	else:
	    #keep multiple purna-viram together
	    text = re.sub(u'(\u0964\u0964+)([^\u0964])', lambda m: r' %sMULTI %s' %('PNVM'*len(m.group(1)), m.group(2)), text)
	    #keep multiple purna deergh-viram together
	    text = re.sub(u'(\u0965\u0965+)([^\u0965])', lambda m: r' %sMULTI %s' %('DGVM'*len(m.group(1)), m.group(2)), text)
        #split contractions right (both "'" and "’")
        text = re.sub(u"([^a-zA-Z\u0080-\u024f])(['\u2019])([^a-zA-Z\u0080-\u024f])", r"\1 \2 \3", text)
        text = re.sub(u"([^a-zA-Z0-9\u0966-\u096f\u0080-\u024f])(['\u2019])([a-zA-Z\u0080-\u024f])", r"\1 \2 \3", text)
        text = re.sub(u"([a-zA-Z\u0080-\u024f])(['\u2019])([^a-zA-Z\u0080-\u024f])", r"\1 \2 \3", text)
        text = re.sub(u"([a-zA-Z\u0080-\u024f])(['\u2019])([a-zA-Z\u0080-\u024f])", r"\1 \2\3", text)
        text = re.sub(u"([0-9\u0966-\u096f])(['\u2019])s", r"\1 \2s", text)
        text = text.replace("''", " ' ' ")

        #handle non-breaking prefixes
        words = text.split()
        text_len = len(words) - 1
        text = str()
        for i,word in enumerate(words):
            if word.endswith('.'):
                dotless = word[:-1]
                if dotless.isdigit():
                    word = dotless + ' .'
                elif ('.' in dotless and re.search('[a-zA-Z]', dotless)) or \
                    self.NBP.get(dotless, 0) == 1 or (i<text_len and words[i+1][0].islower()): pass
                elif self.NBP.get(dotless, 0) == 2 and (i<text_len and words[i+1][0].isdigit()): pass
                elif i < text_len and words[i+1][0].isdigit():
                    if not ENCHANT: pass
                    elif ((len(dotless) > 2) and (self.en_dict.check(dotless.lower()) or \
                        self.en_dict.check(dotless.title()))):
                        word = dotless + ' .'
                else: word = dotless + ' .'
            text += "%s " %word

        if self.dev:
            #seperate out "," except for Hindi and Ascii digits
	    text = re.sub(u'([^0-9\u0966-\u096f]),', r'\1 , ', text)
	    text = re.sub(u',([^0-9\u0966-\u096f])', r' , \1', text)
	    #separate out on Hindi characters followed by non-Hindi characters or purna viram or deergh viram and vice-versa
            text = re.sub(u'([\u0900-\u0965\u0970-\u097f])([^\u0900-\u0965\u0970-\u097f]|[\u0964\u0965])', r'\1 \2', text)
            text = re.sub(u'([^\u0900-\u0965\u0970-\u097f]|[\u0964\u0965])([\u0900-\u0965\u0970-\u097f])', r'\1 \2', text)
        elif self.ben:
            #seperate out "," except for Bengali and Ascii digits
	    text = re.sub(u'([^0-9\u09e6-\u09ef]),', r'\1 , ', text)
	    text = re.sub(u',([^0-9\u09e6-\u09ef])', r' , \1', text)
	    #separate out on Bengali characters followed by non-Bengali characters or purna viram or deergh viram and vice-versa
            text = re.sub(u'([\u0980-\u09e5\u09f0-\u09ff])([^\u0980-\u09e5\u09f0-\u09ff]|[\u0964-\u0965])', r'\1 \2', text)
            text = re.sub(u'([^\u0980-\u09e5\u09f0-\u09ff]|[\u0964-\u0965])([\u0980-\u09e5\u09f0-\u09ff])', r'\1 \2', text)
            #seperate out Bengali special chars (currency signs, BENGALI ISSHAR)
            text = re.sub(u'([\u09f2\u09f3\u09fa\u09fb])', r' \1 ', text)
        elif self.guj:
            #seperate out "," except for Gujrati and Ascii digits
	    text = re.sub(u'([^0-9\u0ae6-\u0aef]),', r'\1 , ', text)
	    text = re.sub(u',([^0-9\u0ae6-\u0aef])', r' , \1', text)
	    #separate out on Gujrati characters followed by non-Gujrati characters or purna viram or deergh viram and vice-versa
            text = re.sub(u'([\u0A80-\u0AE5\u0Af0-\u0Aff])([^\u0A80-\u0AE5\u0Af0-\u0Aff]|[\u0964-\u0965])', r'\1 \2', text)
            text = re.sub(u'([^\u0A80-\u0AE5\u0Af0-\u0Aff]|[\u0964-\u0965])([\u0A80-\u0AE5\u0Af0-\u0Aff])', r'\1 \2', text)
            #seperate out Gujurati special chars (currency signs, GUJARATI OM)
            text = re.sub(u'([\u0AD0\u0AF1])', r' \1 ', text)
        elif self.mal:
            #seperate out "," except for Malayalam and Ascii digits
	    text = re.sub(u'([^0-9\u0d66-\u0d6f]),', r'\1 , ', text)
	    text = re.sub(u',([^0-9\u0d66-\u0d6f])', r' , \1', text)
	    #separate out on Malayalam characters followed by non-Malayalam characters or purna viram or deergh viram and vice-versa
            text = re.sub(u'([\u0D00-\u0D65\u0D73-\u0D7f])([^\u0D00-\u0D65\u0D73-\u0D7f]|[\u0964-\u0965])', r'\1 \2', text)
            text = re.sub(u'([^\u0D00-\u0D65\u0D73-\u0D7f]|[\u0964-\u0965])([\u0D00-\u0D65\u0D73-\u0D7f])', r'\1 \2', text)
            #seperate out Malayalam fraction symbols
            text = re.sub(u'([\u0d73\u0d74\u0d75])', r' \1 ', text)
        elif self.pan:
            #seperate out "," except for Punjabi and Ascii digits
	    text = re.sub(u'([^0-9\u0a66-\u0a6f]),', r'\1 , ', text)
	    text = re.sub(u',([^0-9\u0a66-\u0a6f])', r' , \1', text)
	    #separate out on Punjabi characters followed by non-Punjabi characters or purna viram or deergh viram and vice-versa
            text = re.sub(u'([\u0A00-\u0A65\u0A70-\u0A7f])([^\u0A00-\u0A65\u0A70-\u0A7f]|[\u0964-\u0965])', r'\1 \2', text)
            text = re.sub(u'([^\u0A00-\u0A65\u0A70-\u0A7f]|[\u0964-\u0965])([\u0A00-\u0A65\u0A70-\u0A7f])', r'\1 \2', text)
        elif self.tel:
            #seperate out "," except for Telugu and Ascii digits
	    text = re.sub(u'([^0-9\u0c66-\u0c6f]),', r'\1 , ', text)
	    text = re.sub(u',([^0-9\u0c66-\u0c6f])', r' , \1', text)
	    #separate out on Telugu characters followed by non-Telugu characters or purna viram or deergh viram and vice-versa
            text = re.sub(u'([\u0c00-\u0c65\u0c70-\u0c7f])([^\u0c00-\u0c65\u0c70-\u0c7f]|[\u0964-\u0965])', r'\1 \2', text)
            text = re.sub(u'([^\u0c00-\u0c65\u0c70-\u0c7f]|[\u0964-\u0965])([\u0c00-\u0c65\u0c70-\u0c7f])', r'\1 \2', text)
            #separate out Telugu fractions and weights
            text = re.sub(u'([\u0c78-\u0c7f])', r' \1 ', text)
        elif self.tam:
            #seperate out "," except for Tamil and Ascii digits
	    text = re.sub(u'([^0-9\u0be6-\u0bef]),', r'\1 , ', text)
	    text = re.sub(u',([^0-9\u0be6-\u0bef])', r' , \1', text)
	    #separate out on Tamil characters followed by non-Tamil characters or purna viram or deergh viram and vice-versa
            text = re.sub(u'([\u0B80-\u0Be5\u0Bf3-\u0Bff])([^\u0B80-\u0Be5\u0Bf3-\u0Bff]|[\u0964-\u0965])', r'\1 \2', text)
            text = re.sub(u'([^\u0B80-\u0Be5\u0Bf3-\u0Bff]|[\u0964-\u0965])([\u0B80-\u0Be5\u0Bf3-\u0Bff])', r'\1 \2', text)
            #seperate out Tamil special symbols (calendrical, clerical, currency signs etc.)
            text = re.sub(u'([\u0bd0\u0bf3-\u0bff])', r' \1 ', text)
        elif self.kan:
            #seperate out "," except for Kanadda and Ascii digits
	    text = re.sub(u'([^0-9\u0ce6-\u0cef]),', r'\1 , ', text)
	    text = re.sub(u',([^0-9\u0ce6-\u0cef])', r' , \1', text)
	    #separate out on Kanadda characters followed by non-Kanadda characters or purna viram or deergh viram and vice-versa
            text = re.sub(u'([\u0C80-\u0Ce5\u0Cf1-\u0Cff])([^\u0C80-\u0Ce5\u0Cf1-\u0Cff]|[\u0964-\u0965])', r'\1 \2', text)
            text = re.sub(u'([^\u0C80-\u0Ce5\u0Cf1-\u0Cff]|[\u0964-\u0965])([\u0C80-\u0Ce5\u0Cf1-\u0Cff])', r'\1 \2', text)
        elif self.ori:
            #seperate out "," except for Oriya and Ascii digits
	    text = re.sub(u'([^0-9\u0b66-\u0b6f]),', r'\1 , ', text)
	    text = re.sub(u',([^0-9\u0b66-\u0b6f])', r' , \1', text)
	    #separate out on Oriya characters followed by non-Oriya characters or purna viram or deergh viram and vice-versa
            text = re.sub(u'([\u0B00-\u0B65\u0B70-\u0B7f])([^\u0B00-\u0B65\u0B70-\u0B7f]|[\u0964-\u0965])', r'\1 \2', text)
            text = re.sub(u'([^\u0B00-\u0B65\u0B70-\u0B7f]|[\u0964-\u0965])([\u0B00-\u0B65\u0B70-\u0B7f])', r'\1 \2', text)
            #seperate out Oriya fraction symbols
	    text = re.sub(u'([\u0B72-\u0B77])', r' \1 ', text)
	elif self.urd:
	    #seperate out urdu full-stop i.e., "۔"
	    text = text.replace(u'\u06d4', u' \u06d4 ')
	    #seperate out urdu quotation marks i.e., "٬"
	    text = text.replace(u'\u066c', u' \u066c ')
	    #seperate out Urdu comma i.e., "،" except for Urdu digits
	    text = re.sub(u'([^\u0660-\u0669\u06f0-\u06f9])\u060C', ur'\1 \u060C ', text)
	    text = re.sub(u'\u060C([^\u0660-\u0669\u06f0-\u06f9])', ur' \u060C \1', text)
	    #separate out on Urdu characters followed by non-Urdu characters and vice-versa
	    text = re.sub(u'([\u0617-\u061a\u0620-\u065f\u066e-\u06d3\u06d5\u06fa-\u06ff])' +
			    u'([^\u0617-\u061a\u0620-\u065f\u066e-\u06d3\u06d5\u06fa-\u06ff])', r'\1 \2', text)
	    text = re.sub(u'([^\u0617-\u061a\u0620-\u065f\u066e-\u06d3\u06d5\u06fa-\u06ff])' +
			    u'([\u0617-\u061a\u0620-\u065f\u066e-\u06d3\u06d5\u06fa-\u06ff])', r'\1 \2', text)
	    #separate out on every other special character
	    text = re.sub(u'([\u0600-\u0607\u0609\u060a\u060d\u060e\u0610-\u0614\u061b-\u061f\u066a-\u066d\u06dd\u06de\u06e9])', 
			    r' \1 ', text)

	if not self.urd:
	    #Normalize "|" to purna viram 
	    text = text.replace('|', u'\u0964')
	    #Normalize ". ।" to "।"
	    text = re.sub(u'\.\s+\u0964', u'\u0964', text)
       
     #   text = re.sub('(-+)', lambda m: r'%s' %(' '.join('-'*len(m.group(1)))), text) 
        text = re.sub('(-+)', lambda m: r'%s' %('\n'.join('-'*len(m.group(1)))), text) 
        if self.dev:
            text = re.sub(u'(-?[0-9\u0966-\u096f]-+[0-9\u0966-\u096f]-?){,}',lambda m: r'%s' %(m.group().replace('-', ' - ')), text)
        elif self.ben:
            text = re.sub(u'(-?[0-9\u09e6-\u09ef]-+[0-9\u09e6-\u09ef]-?){,}',lambda m: r'%s' %(m.group().replace('-', ' - ')), text)
        elif self.guj:
            text = re.sub(u'(-?[0-9\u0ae6-\u0aef]-+[0-9\u0ae6-\u0aef]-?){,}',lambda m: r'%s' %(m.group().replace('-', ' - ')), text)
        elif self.mal:
            text = re.sub(u'(-?[0-9\u0d66-\u0D72]-+[0-9\u0d66-\u0D72]-?){,}',lambda m: r'%s' %(m.group().replace('-', ' - ')), text)
        elif self.pan:
            text = re.sub(u'(-?[0-9\u0a66-\u0a6f]-+[0-9\u0a66-\u0a6f]-?){,}',lambda m: r'%s' %(m.group().replace('-', ' - ')), text)
        elif self.tel:
            text = re.sub(u'(-?[0-9\u0c66-\u0c6f]-+[0-9\u0c66-\u0c6f]-?){,}',lambda m: r'%s' %(m.group().replace('-', ' - ')), text)
        elif self.tam:
            text = re.sub(u'(-?[0-9\u0be6-\u0bf2]-+[0-9\u0be6-\u0bf2]-?){,}',lambda m: r'%s' %(m.group().replace('-', ' - ')), text)
        elif self.kan:
            text = re.sub(u'(-?[0-9\u0ce6-\u0cef]-+[0-9\u0ce6-\u0cef]-?){,}',lambda m: r'%s' %(m.group().replace('-', ' - ')), text)
        elif self.ori:
            text = re.sub(u'(-?[0-9\u0b66-\u0b6f]-+[0-9\u0b66-\u0b6f]-?){,}',lambda m: r'%s' %(m.group().replace('-', ' - ')), text)
        elif self.urd:
            text = re.sub(u'(-?[0-9\u0660-\u0669\u06f0-\u06f9]-+[0-9\u0660-\u0669\u06f0-\u06f9]-?){,}',
			    lambda m: r'%s' %(m.group().replace('-', ' - ')), text)
        #text = ' '.join(text.split())
        text = '\n'.join(text.split())
        #restore multiple dots, purna virams and deergh virams
        text = re.sub(r'(DOT)(\1*)MULTI', lambda m: r'.%s' %('.'*(len(m.group(2))/3)), text)
	if self.urd:
	    text = re.sub(r'(DOTU)(\1*)MULTI', lambda m: u'\u06d4%s' %(u'\u06d4'*(len(m.group(2))/3)), text)
	else:
	    text = re.sub(r'(PNVM)(\1*)MULTI', lambda m: u'\u0964%s' %(u'\u0964'*(len(m.group(2))/4)), text)
	    text = re.sub(r'(DGVM)(\1*)MULTI', lambda m: u'\u0965%s' %(u'\u0965'*(len(m.group(2))/4)), text)

	#split sentences
	if self.urd: 
	    text = re.sub(u' ([!.?\u06d4]) ([\u0617-\u061a\u0620-\u065f\u066e-\u06d3\u06d5\u06fa-\u06ffa-zA-Z])', r' \1\n\2', text)
	    text = re.sub(u' ([!.?\u06d4]) ([\(\{\[\'"\u2018\u201c<]) ', r' \1 \2\n', text)
	    #text = re.sub(u' ([!.?\u06d4]) ([^\u0617-\u061a\u0620-\u065f\u066e-\u06d3\u06d5\u06fa-\u06ffa-zA-Z]) ', r' \1 \2\n', text)
	else: 
	    text = re.sub(u' ([!.?\u0964\u0965]) ([\u0900-\u0d7fa-zA-Z])', r' \1\n\2', text)
	    text = re.sub(u' ([!.?\u0964\u0965]) ([\)\}\]\'"\u2019\u201d>]) ', r' \1 \2\n', text)
	    #text = re.sub(u' ([!.?\u0964\u0965]) ([^\u0900-\u0d7fa-zA-Z]) ', r' \1 \2\n', text)
        
        return text

if __name__ == '__main__':
    
    lang_help = """select language (3 letter ISO-639 code)
		Hindi       : hin
		Urdu	    : urd
		Telugu      : tel
		Tamil       : tam
		Malayalam   : mal
		Kannada     : kan
		Bengali     : ben
		Oriya       : ori
		Punjabi     : pan
		Marathi     : mar
		Nepali      : nep
		Gujarati    : guj
		Bodo        : bod
		Konkani     : kok
		Assamese    : asm"""
    languages = "hin urd ben asm guj mal pan tel tam kan ori mar nep bod kok".split()
    # parse command line arguments 
    parser = argparse.ArgumentParser(prog="indic_tokenizer", 
                                    description="Tokenizer for Indian Scripts",
                                    formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--i', metavar='input', dest="INFILE", type=argparse.FileType('r'), default=sys.stdin, help="<input-file>")
    parser.add_argument('--l', metavar='language', dest="lang", choices=languages, default='hin', help=lang_help)
    parser.add_argument('--o', metavar='output', dest="OUTFILE", type=argparse.FileType('w'), default=sys.stdout, help="<output-file>")
    args = parser.parse_args()

    # initialize convertor object
    tzr = tokenizer(lang=args.lang)
    # convert data
    for line in args.INFILE:
        line = line.decode('utf-8')
        line = tzr.normalize(line)
        line = tzr.tokenize(line)
        line = line.encode('utf-8')
        args.OUTFILE.write('%s\n$$$\n' %line)

    # close files 
    args.INFILE.close()
    args.OUTFILE.close()
