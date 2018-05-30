import itertools
from functools import reduce
from fuzzywuzzy import fuzz
import numpy as np
import scipy
import scipy.spatial
import scipy.cluster
import scipy.stats
import random
import os


def generateRandomColor():
	_min = 0
	_max = 200
	r = random.randint(_min, _max)
	g = random.randint(_min, _max)
	b = random.randint(_min, _max)
	c = "#{:>02X}{:>02X}{:>02X}".format(r, g, b)
	return c


def getcommonletters(strlist):
	return ''.join([x[0] for x in zip(*strlist) if reduce(lambda a, b: (a == b) and a or None, x)])


def findcommonstart(strlist):
	strlist = strlist[:]
	prev = None
	while True:
		common = getcommonletters(strlist)
		if common == prev:
			break
		strlist.append(common)
		prev = common

	return getcommonletters(strlist)


class BuildTree:
	"""
		Parameters
		----------
			method: {'single', 'complete', 'average', 'weighted', 'centroid', 'median', 'ward'}
	"""

	def __init__(self, array, method = 'single'):
		self.method = method
		self.color_map = dict()
		self.cluster_map = dict()
		self.array = np.asarray(sorted([i.lower().strip() for i in array]))

		self.ratio_map, self.distance_map = self._generateDistanceMap(self.array)

		lev_distance = [[self.getDistance(i, j) for j in self.array] for i in self.array]
		lev_distance = np.asarray(lev_distance)

		upper_triangle = scipy.spatial.distance.squareform(lev_distance)

		self.linkage_clusters = scipy.cluster.hierarchy.linkage(
			upper_triangle,
			method = self.method,
			optimal_ordering = True
		)

		self.root = scipy.cluster.hierarchy.to_tree(self.linkage_clusters)

	def _getSubClusters(self, cluster):
		children = [cluster.id]
		if not cluster.is_leaf():
			children += self._getSubClusters(cluster.get_left())
			children += self._getSubClusters(cluster.get_right())
		return children

	@staticmethod
	def _calculateRatio(i, j):
		a, b = sorted([i, j])
		# ratio = fuzz.token_sort_ratio(a, b)
		ratio = fuzz.WRatio(a, b)
		return ratio

	def _generateDistanceMap(self, array):
		ratio_map = dict()

		for i, j in itertools.product(array, repeat = 2):
			ratio = self._calculateRatio(i, j)
			ratio_map[(i, j)] = ratio
		todistance = lambda s: (100 - s) / 100
		distance_map = {key: todistance(value) for key, value in ratio_map.items()}
		return ratio_map, distance_map

	def _addClusterColor(self, cluster):
		color = generateRandomColor()
		cluster_children = self._getSubClusters(cluster)

		for i in cluster_children:
			self.color_map[i] = color


	def _getLeafs(self, indicies):
		return [self.array[i] for i in indicies if i < len(self.array)]

	@property
	def Z(self):
		return self.linkage_clusters

	def getDistance(self, i, j):
		return self.distance_map[(i, j)]

	def getRatio(self, i, j):
		return self.ratio_map[(i, j)]

	def analyzeHierarchy(self, tree = None, parent = None, score_cutoff = 85, **kwargs):

		if tree is None:
			tree = self.root
		tree_metrics = self.getClusterMetrics(tree, parent)
		self.cluster_map[tree.id] = tree_metrics
		score = tree_metrics['clusterScore']
		common_substring = findcommonstart(tree_metrics['clusterLeafs'])

		is_similar = score >= score_cutoff
		tree_name = self.array[tree.id] if tree.id < len(self.array) else tree.id

		is_group = is_similar
		if is_group:
			self._addClusterColor(tree)
			if False:
				print("{} ({:.2f}): {}".format(tree_metrics['clusterId'], score, common_substring))
				for leaf in tree_metrics['clusterLeafs']:
					# _leaf_comparison = [self.getRatio(leaf, i) for i in tree_metrics['clusterLeafs']]
					# _comparison = '|'.join([str(i) for i in _leaf_comparison])
					_comparison = ''
					print("\t{} ({})".format(leaf, _comparison))
		else:
			self.color_map[tree.id] = '#DDDDDD'
			left = tree.get_left()
			right = tree.get_right()
			if left and right and False:
				print("{} ({}, {})|({}, {})".format(tree.id, left.id, left.count, right.id, right.count))
			if left is not None:
				self.analyzeHierarchy(left, parent = tree)
			if right is not None:
				self.analyzeHierarchy(right, parent = tree)

	def getClusterMetrics(self, cluster, parent = None):
		children = cluster.pre_order(lambda s: s.id)
		leafs = self._getLeafs(children)

		leaf_ratios = list()
		leaf_distances = list()
		for i, j in itertools.product(leafs, repeat = 2):
			leaf_ratios.append( self.getRatio(i, j))
			leaf_distances.append(self.getDistance(i, j))

		average_ratio = sum(leaf_ratios) / len(leaf_ratios)

		if parent:
			distance_from_parent = parent.dist - cluster.dist
		else:
			distance_from_parent = 0

		metrics = {
			'cluster': cluster,
			'clusterId':     cluster.id,
			'clusterName':   findcommonstart(leafs),
			'clusterLeafs':  leafs,
			'clusterScore':  average_ratio,
			'clusterRatios': leaf_ratios,
			'clusterDistances': leaf_distances,
			'clusterDistance': cluster.dist,
			'parent': parent,
			'distanceFromParent': distance_from_parent
		}

		return metrics

	def savefig(self, **kwargs):
		import matplotlib.pyplot as plt

		orientation = kwargs.get('orientation', 'left')

		def leafFunc(cluster_id, cluster_map = self.cluster_map):
			cluster = cluster_map[cluster_id]
			if cluster_id < len(self.array):
				string = self.array[cluster_id]
				label = "{} - {}".format(cluster['distanceFromParent'], string)
			else:
				label = 'Non-leaf'
			return label

		if orientation in ['left', 'right']:
			figsize = (20, 40)
			label_rotation = 45
		else:
			label_rotation = 45
			figsize = (40, 20)

		fig, ax = plt.subplots(figsize = figsize)
		scipy.cluster.hierarchy.dendrogram(
			self.Z,
			orientation = orientation,
			ax = ax,
			#labels = self.array,
			color_threshold = 0.00005,
			link_color_func = lambda s: self.color_map[s],
			leaf_rotation = label_rotation,
			leaf_font_size = 10,
			leaf_label_func = leafFunc
		)
		fname = os.path.join(os.path.dirname(__file__), "hierarchy.{}.png".format(self.method))
		plt.savefig(fname, dpi = 300)

if __name__ == "__main__":
	crash = [
		"let's watch - crash 2 - back from the dead (finale)",
		"let's watch - crash 2 - can they bear it? (part 2)",
		"let's watch - crash 2 - enter the warp room (part 1)",
		"let's watch - crash 2 - jeremy forgets everything (part 3)",
		"let's watch - crash 2 - not the bees (part 4)",
		"let's watch - crash 3: warped - almost good (part 2)",
		"let's watch - crash 3: warped - dog at dog fighting (part 4)",
		"let's watch - crash 3: warped - gavin gets bunced (finale)",
		"let's watch - crash 3: warped - gavin loves bum (part 3)",
		"let's watch - crash 3: warped- gavin unleashed (part 1)",
		"let's watch - crash bandicoot - dr. neo cortex (finale)",
		"let's watch - crash bandicoot - going hog wild! (#1)",
		"let's watch - crash bandicoot - the moonshine episode (#3)",
		"let's watch - crash bandicoot - the secret levels"
	]

	crash_tree = BuildTree(crash)
	crash_tree.analyzeHierarchy()
	crash_tree.savefig()


