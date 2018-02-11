# -*- coding: utf-8 -*-
#!/usr/bin/env python

import sys
import community_ext
import networkx as nx
from collections import defaultdict
import scipy
from math import log

fn = "datasets/polblogs/polblogs.edges"
print "DATASET:",fn

# load graph
G = nx.Graph()
for line in open(fn):
    from_node, to_node = map(int, line.rstrip().split("\t"))
    if from_node not in G or to_node not in G[from_node]:
        G.add_edge(from_node,to_node)

# load the ground-truth partition and the precalculated louvain partition
fn1 = fn.replace(".edges",".clusters")
fn2 = fn.replace(".edges",".louvain")
groundtruth_partition = dict()
for line in open(fn1):
    node, cluster = map(int, line.rstrip().split("\t"))
    if node not in G.nodes(): continue 
    groundtruth_partition[node] = cluster
louvain_partition = dict()
for line in open(fn2):
    node, cluster = map(int, line.rstrip().split("\t"))
    if node not in G.nodes(): continue 
    louvain_partition[node] = cluster

# print some general info
gt_mu = community_ext.estimate_mu(G,groundtruth_partition)
print "ground truth mu\t",gt_mu
print "ground truth clusters\t",len(set(groundtruth_partition.values()))
print "ground truth modularity\t", community_ext.modularity(groundtruth_partition,G)
print 
l_mu = community_ext.estimate_mu(G,louvain_partition)
print "louvain clusters\t",len(set(louvain_partition.values()))
print "louvain modularity\t", community_ext.modularity(louvain_partition,G)
part_scores = community_ext.compare_partitions(groundtruth_partition,louvain_partition)
print 'louvain vs ground truth: rand\t',part_scores['rand'] 
print 'louvain vs ground truth: jaccard\t',part_scores['jaccard'] 
print 'louvain vs ground truth: nmi\t',part_scores['nmi'] 
print 


# now cycle thru the methods and optimize with each one
methods = ('ppm','dcppm','ilfrs')

for method in methods:
    print '\nMethod', method
    # a starting parameter value depends on the method
    if method in ('ilfrs',):
        work_par = 0.5
    else:
        work_par = 1.

    # now start the iterative process    
    prev_par, it = -1, 0
    prev_pars = set()
    while abs(work_par-prev_par)>1e-5: # stop if the size of improvement too small
        it += 1
        if it>100: break # stop after 100th iteration

        # update the parameter value
        prev_par = work_par
        if prev_par in prev_pars: break # stop if we are in the cycle
        prev_pars.add(prev_par)

        # find the optimal partition with the current parameter value
        if method in ('ilfrs',):
            partition = community_ext.best_partition(G,model=method,pars={'mu':work_par})
        else:
            partition = community_ext.best_partition(G,model=method,pars={'gamma':work_par})

        # calculate optimal parameter value for the current partition
        if method in ('ilfrs',):
            work_par = community_ext.estimate_mu(G,partition)
        else:
            work_par = community_ext.estimate_gamma(G,partition,model=method)
        loglike =   community_ext.model_log_likelihood(G,partition,model=method,pars={'gamma':work_par,'mu':work_par})
        print 'current par',work_par,'loglike',loglike

    # calculate and print the scores of resulting partition
    part_scores = community_ext.compare_partitions(groundtruth_partition,partition)
    loglike =   community_ext.model_log_likelihood(G,partition,model=method,pars={'gamma':work_par,'mu':work_par})
    print 'best par',work_par
    print " ".join(map(str,['rand\t',part_scores['rand'],'\tjaccard\t',part_scores['jaccard'],'\tnmi\t',\
                            part_scores['nmi'],"\tsize\t",len(set(partition.values())),'loglike',loglike]))
