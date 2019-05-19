import random
import os

screenshots_folder = '../screenshot_emails/'
prefix = 'highlightdisk/screenshot_emails/'  # proxy and folder in yadisk
files = os.listdir(screenshots_folder + 'random')
pairs = [('tf_idf_pos_share_04', 'tf_idf_pos_share_05')]  #, ('tf_idf_embeddings', 'gensim_sentences'), 'gensim_keywords', 'embeddings']

honeypot_algs = ['tf_idf_embeddings',
                 'tf_idf_custom', 'tf_idf_pos']
honeypot_final_share = 0.2
n_real_tasks = len(pairs) * len(files) * 2
honeypot_files = random.choices(files, k=round(
    n_real_tasks / (1 - honeypot_final_share) * honeypot_final_share
))


with open('tf_idf_pos_share_04_vs_tf_idf_pos_share_05.tsv', 'w') as f:
    f.write('INPUT:image_left	INPUT:image_right	GOLDEN:result	HINT:text\n')
    for pair in pairs:
        filelists = [os.listdir(screenshots_folder + alg) for alg in pair]
        for filename in files:
            for filelist in filelists:
                assert filename in filelist
            line1 = [prefix + '/'.join([alg, filename]) for alg in pair]
            line2 = [prefix + '/'.join([alg, filename]) for alg in pair[::-1]]
            f.write('\t'.join(line1 + ['', '']) + '\n')
            f.write('\t'.join(line2 + ['', '']) + '\n')
    for filename in honeypot_files:
        goodalg = random.choice(honeypot_algs)
        line = [prefix + '/'.join([alg, filename]) 
                 for alg in ['random', goodalg]]
        rev = random.random() > 0.5
        gold = 'right' if not rev else 'left'
        if rev:
            line.reverse()
        line.append(gold)
        f.write('\t'.join(line + ['']) + '\n')
