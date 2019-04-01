import random
import os

screenshots_folder = '../screenshot_emails/'
prefix = 'highlightdisk/screenshot_emails/'  # proxy and folder in yadisk
files = os.listdir(screenshots_folder + 'random')
algs = ['embeddings', 'gensim_sentences',
        'tf_idf_embeddings', 'tf_idf_custom', 'gensim_keywords']
with open('task_quaterfinal.tsv', 'w') as f:
    f.write('INPUT:image_left	INPUT:image_right	GOLDEN:result	HINT:text\n')
    for pair in [('tf_idf_embeddings', 'tf_idf_custom')]: #, ('embeddings', 'gensim_sentences'), 'gensim_keywords']:
        filelists = [os.listdir(screenshots_folder + alg) for alg in pair]
        for filename in files:
            for filelist in filelists:
                assert filename in filelist
            line1 = [prefix + '/'.join([alg, filename]) for alg in pair]
            line2 = [prefix + '/'.join([alg, filename]) for alg in pair[::-1]]
            f.write('\t'.join(line1 + ['', '']) + '\n')
            f.write('\t'.join(line2 + ['', '']) + '\n')
    for filename in files:
        goodalg = random.choice(algs)
        line = [prefix + '/'.join([alg, filename]) 
                 for alg in ['random', goodalg]]
        rev = random.random() > 0.5
        gold = 'right' if not rev else 'left'
        if rev:
            line.reverse()
        line.append(gold)
        f.write('\t'.join(line + ['']) + '\n')
