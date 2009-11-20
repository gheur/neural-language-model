#!/usr/bin/env python

import sys
import string
import common.dump
from common.file import myopen
from common.stats import stats

import miscglobals
import logging

def get_train_example():
    import common.hyperparameters
    HYPERPARAMETERS = common.hyperparameters.read("language-model")

    from vocabulary import wordmap
    for l in myopen(HYPERPARAMETERS["TRAIN_SENTENCES"]):
        prevwords = []
        for w in string.split(l):
            w = string.strip(w)
            id = None
            if wordmap.exists(w):
                prevwords.append(wordmap.id(w))
                if len(prevwords) >= HYPERPARAMETERS["WINDOW_SIZE"]:
                    yield prevwords[-HYPERPARAMETERS["WINDOW_SIZE"]:]
            else:
                prevwords = []

def get_validation_example():
    import common.hyperparameters
    HYPERPARAMETERS = common.hyperparameters.read("language-model")

    from vocabulary import wordmap
    for l in myopen(HYPERPARAMETERS["VALIDATION_SENTENCES"]):
        prevwords = []
        for w in string.split(l):
            w = string.strip(w)
            if wordmap.exists(w):
                prevwords.append(wordmap.id(w))
                if len(prevwords) >= HYPERPARAMETERS["WINDOW_SIZE"]:
                    yield prevwords[-HYPERPARAMETERS["WINDOW_SIZE"]:]
            else:
                prevwords = []

#ves = [e for e in get_validation_example()]
#import random
#random.shuffle(ves)
#for e in ves[:1000]:
#    print string.join([wordmap.str(id) for id in e])

def validate(cnt):
    import math
    logranks = []
    logging.info("BEGINNING VALIDATION AT TRAINING STEP %d" % cnt)
    logging.info(stats())
    i = 0
    for (i, ve) in enumerate(get_validation_example()):
#        logging.info([wordmap.str(id) for id in ve])
        logranks.append(math.log(m.validate(ve)))
        if (i+1) % 10 == 0:
            logging.info("Training step %d, validating example %d, mean(logrank) = %.2f, stddev(logrank) = %.2f" % (cnt, i+1, numpy.mean(numpy.array(logranks)), numpy.std(numpy.array(logranks))))
            logging.info(stats())
    logging.info("FINAL VALIDATION AT TRAINING STEP %d: mean(logrank) = %.2f, stddev(logrank) = %.2f, cnt = %d" % (cnt, numpy.mean(numpy.array(logranks)), numpy.std(numpy.array(logranks)), i+1))
    logging.info(stats())
#    print "FINAL VALIDATION AT TRAINING STEP %d: mean(logrank) = %.2f, stddev(logrank) = %.2f, cnt = %d" % (cnt, numpy.mean(numpy.array(logranks)), numpy.std(numpy.array(logranks)), i+1)
#    print stats()

def verbose_predict(cnt):
    for (i, ve) in enumerate(get_validation_example()):
        (score, prehidden) = m.verbose_predict(ve)
        abs_prehidden = numpy.abs(prehidden)
        med = numpy.median(abs_prehidden)
        abs_prehidden = abs_prehidden.tolist()
        assert len(abs_prehidden) == 1
        abs_prehidden = abs_prehidden[0]
        abs_prehidden.sort()
        abs_prehidden.reverse()
        logging.info(cnt, "AbsPrehidden median =", med, "max =", abs_prehidden[:5])
        if i > 5: break

def visualize(cnt, WORDCNT=500, randomized=False):
    """
    Visualize a set of examples using t-SNE.
    If randomized=False, visualize the most common words.
    If randomized=True, visualize random words.
    """
    from vocabulary import wordmap
    PERPLEXITY=30

    if randomized:
        import random
        idxs = range(m.parameters.vocab_size)
        random.shuffle(idxs)
        idxs = idxs[:WORDCNT]
    else:
        idxs = range(WORDCNT)

    x = m.parameters.embeddings[idxs]
    print x.shape
    titles = [wordmap.str(id) for id in idxs]
    import os.path
    if randomized:
        filename = os.path.join(rundir, "embeddings-randomized-%d.png" % cnt)
    else:
        filename = os.path.join(rundir, "embeddings-mostcommon-%d.png" % cnt)
    try:
        from textSNE.calc_tsne import tsne
#       from textSNE.tsne import tsne
        out = tsne(x, perplexity=PERPLEXITY)
        from textSNE.render import render
        render([(title, point[0], point[1]) for title, point in zip(titles, out)], filename)
    except IOError:
        logging.info("ERROR visualizing", filename, ". Continuing...")

def embeddings_debug(cnt):
    e = m.parameters.embeddings[:100]
    l2norm = numpy.sqrt(numpy.square(e).sum(axis=1))
    logging.info("%d l2norm of top 100 words: mean = %f stddev=%f" % (cnt, numpy.mean(l2norm), numpy.std(l2norm),))
#    print("%d l2norm of top 100 words: mean = %f stddev=%f" % (cnt, numpy.mean(l2norm), numpy.std(l2norm),))
    l2norm = l2norm.tolist()
    l2norm.sort()
    l2norm.reverse()
    logging.info("top 5 = %s" % `l2norm[:5]`)
#    print("top 5 = %s" % `l2norm[:5]`)

def save_state(m, cnt):
    import os.path
    filename = os.path.join(rundir, "model-%d.pkl" % cnt)
    logging.info("Writing model to %s..." % filename)
    logging.info(stats())
    import cPickle
    cPickle.dump(m, myopen(filename, "wb"), protocol=-1)
    logging.info("...done writing model to %s" % filename)
    logging.info(stats())

if __name__ == "__main__":
    import common.hyperparameters, common.options
    HYPERPARAMETERS = common.hyperparameters.read("language-model")
    HYPERPARAMETERS, options, args, newkeystr = common.options.reparse(HYPERPARAMETERS)
    import hyperparameters

    from common import myyaml
    import sys
    print >> sys.stderr, myyaml.dump(common.dump.vars_seq([hyperparameters, miscglobals]))

    import noise
    indexed_weights = noise.indexed_weights()

    rundir = common.dump.create_canonical_directory(HYPERPARAMETERS)

    import os.path, os
    logfile = os.path.join(rundir, "log")
    if newkeystr != "":
        verboselogfile = os.path.join(rundir, "log%s" % newkeystr)
        print >> sys.stderr, "Logging to %s, and creating link %s" % (logfile, verboselogfile)
        os.system("ln -s log %s " % (verboselogfile))
    else:
        print >> sys.stderr, "Logging to %s, not creating any link because of default settings"
    #logging.basicConfig(filename=logfile,level=logging.DEBUG)
    logging.basicConfig(filename=logfile, filemode="w", level=logging.DEBUG)
    logging.info(myyaml.dump(common.dump.vars_seq([hyperparameters, miscglobals])))

    import random, numpy
    random.seed(miscglobals.RANDOMSEED)
    numpy.random.seed(miscglobals.RANDOMSEED)

    import vocabulary
#    logging.info("Reading vocab")
#    vocabulary.read()
    
    import model
    m = model.Model()
    #validate(0)
#    verbose_predict(0)
    embeddings_debug(0)
    epoch = 0
    cnt = 0
    while 1:
        epoch += 1
        logging.info("STARTING EPOCH #%d" % epoch)
        for e in get_train_example():
            cnt += 1
        #    print [wordmap.str(id) for id in e]
            m.train(e)

            #validate(cnt)
            if cnt % 1000 == 0:
                logging.info("Finished training step %d (epoch %d)" % (cnt, epoch))
#                print ("Finished training step %d (epoch %d)" % (cnt, epoch))
            if cnt % 10000 == 0:
                logging.info(stats())
#                verbose_predict(cnt)
                embeddings_debug(cnt)
            if cnt % HYPERPARAMETERS["VALIDATE_EVERY"] == 0:
                save_state(m, cnt)
                visualize(cnt, randomized=False)
                visualize(cnt, randomized=True)
                validate(cnt)
