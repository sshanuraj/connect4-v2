import numpy as np 
import random as rd 

from c4Grid import c4Grid

INF = 1000000

RED = 2
YELLOW = 1

class Node:
	def __init__(self, total_score, ni, parent, state, cols, moveCnt):
		self.t = total_score
		self.n = ni
		self.parent = parent
		self.children = []
		self.n_actions = 7

		self.state = state
		self.cols = cols
		self.moveCnt = moveCnt

		self.isTerminal = False
		self.winColor = 0

	def showParams(self):
		print("Total score: %s"%(str(self.t)))
		print("Total visits: %s"%(str(self.n)))
		print("Grid: \n", self.state)
		print("Column values: \n", self.cols)
		print("Move count: %s"%(str(self.moveCnt)))
		print("Is Terminal: %s"%(str(self.isTerminal)))

	def showStates(self):
		if len(self.children) == 0:
			print(None)
		else:
			k = 0
			for node in self.children:
				print("---- State %s ----"%(str(k+1)))
				print(node.state)
				print()
				k += 1

	def goUp(self):
		return self.parent

	def populateNode(self, player):
		if self.isTerminal:
			return None

		grid = c4Grid()

		for i in range(self.n_actions):
			cols = self.cols.copy()
			if cols[i] <= -1: #check if valid move 
				self.children.append(None)
				continue

			next_state = self.state.copy()  #copying next state for child node
			next_state[cols[i]][i] = player  #making move for child node state
			
			node = Node(0, 0, self, next_state, cols, self.moveCnt+1)

			if grid.checkWinVirtual(next_state, cols[i], i):
				node.isTerminal = True
				node.winColor = player #win for RED/YELLOW

			if node.moveCnt == 42:
				node.isTerminal = True
				node.winColor = -1 #draw
			node.cols[i] -= 1

			self.children.append(node)

	def calculateUCB(self, N):
		if self.n == 0:
			return INF
		ucb = (self.t/self.n) + (np.log(N)/self.n)**0.5
		return ucb

	def getMaxUcbNode(self, N):
		ucbs = []

		if self.isTerminal:
			return None

		inc = 0

		for node in self.children:
			if node:
				ucbs.append(node.calculateUCB(N))
			else:
				ucbs.append(None)

		max_ind = 0
		max_val = -1*INF
		l = len(self.children)
		for i in range(l):
			if ucbs[i] != None and ucbs[i] > max_val:
				max_ind = i
				max_val = ucbs[i]

		max_node = self.children[max_ind]
		return max_node, max_ind

	def getMinUcbNode(self, N):
		ucbs = []

		if self.isTerminal:
			return None

		for node in self.children:
			if node:
				ucbs.append(node.calculateUCB(N))
			else:
				ucbs.append(None)

		min_ind = 0
		min_val = INF+1
		l = len(self.children)
		for i in range(l):
			if ucbs[i] != None and ucbs[i] < min_val:
				min_ind = i
				min_val = ucbs[i]

		min_node = self.children[min_ind]
		return min_node, min_ind

	def checkLeaf(self):
		if len(self.children) == 0:
			return True
		return False

	def backpropagate(self, reward):
		self.n += 1
		self.t += reward
		curr = self.parent

		while curr:
			curr.n += 1
			curr.t += reward
			curr = curr.goUp()

class c4Agent:
	def __init__(self, color):
		self.color = color

	def getReward(self, winColor):
		if winColor == -1:
			return 9

		if self.color == winColor:
			return 20 #for win
		return 0 #for loss

	def makeRandomVirtualMove(self, state, cols, color):
		ok = True
		action = -1
		while ok:
			action = rd.randrange(7)
			if cols[action] >= 0 :
				ok = False

		state[cols[action]][action] = color
		x = cols[action]
		y = action
		cols[action] -= 1

		return state, cols, x, y

	def switchColor(self, color):
		if color == RED:
			return YELLOW
		return RED


	def rollout(self, vgrid, vcols, moveCnt, colorToMove):
		grid = c4Grid()

		while True:
			vgrid, vcols, x, y = self.makeRandomVirtualMove(vgrid, vcols, colorToMove)
			
			moveCnt += 1
			if moveCnt == 42:
				return 9 #draw reward

			if grid.checkWinVirtual(vgrid, x, y):
				return self.getReward(colorToMove) #return win 

			colorToMove = self.switchColor(colorToMove)

	def getBestMove(self, node, n_iterations, N, grid):
		next_node = None
		action = 0
		count = 0 
		if node.checkLeaf():
			node.populateNode(self.color)
		curr = node
		change = False

		if node.isTerminal:
			print("It is terminal node which has been wrongly sent.", node.winColor)
			node.showParams()

		while count < n_iterations:
			if not change: #to reset curr to the initial node
				curr = node
			if curr.checkLeaf():
				print("in leaf node")
				if curr.n == 0:
					#start rollout
					if curr.isTerminal:
						print("is terminal in leaf")
						reward = self.getReward(curr.winColor)
						print("Backpropagate reward")
						curr.backpropagate(reward)
						N += 1
						
						count += 1
						change = False
						continue
					else:
						print("rollout in first visit")
						vgrid = curr.state.copy()
						vcols = curr.cols.copy()
						colorToMove = YELLOW if curr.moveCnt%2 == 1 else RED
						reward = self.rollout(vgrid, vcols, curr.moveCnt, colorToMove)
						print("Backpropagate reward")
						curr.backpropagate(reward)
						N += 1
						
						count += 1
						change = False
						continue
				else:
					#get node
					colorToMove = YELLOW if curr.moveCnt%2 == 1 else RED
					print("Expansion in visited node")

					if curr.isTerminal:
						print("is terminal in leaf")
						reward = self.getReward(curr.winColor)
						print("Backpropagate reward")
						curr.backpropagate(reward)
						N += 1
						
						count += 1
						change = False
						continue

					curr.populateNode(colorToMove)

					if self.color == RED:
						curr, _ = curr.getMaxUcbNode(N)
					else:
						curr, _ = curr.getMinUcbNode(N)

					vgrid = curr.state.copy()
					vcols = curr.cols.copy()

					colorToMove = YELLOW if curr.moveCnt%2 == 1 else RED

					print("Rollout in through expanded node")
					reward = self.rollout(vgrid, vcols, curr.moveCnt, colorToMove)
					print("Backpropagate reward")
					curr.backpropagate(reward)
					N += 1
					
					count += 1
					change = False
					continue

			else:
				change = True
				if self.color == RED:
					print("going to max node")
					curr, _ = curr.getMaxUcbNode(N)
				else:
					print("going to min ucb node")
					curr, _ = curr.getMinUcbNode(N)

		if self.color == RED:
			next_node, action = node.getMaxUcbNode(N)
		else:
			next_node, action = node.getMinUcbNode(N) 
		print("sending action %s and next node"%(str(action)))
		return action

