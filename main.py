#!/usr/bin/env python

'''
Author: Zach Goins
Date: 05/01/2016
Email:zach.a.goins@gmail.com

'''
import numpy,math
from time import sleep
import threading
import sys
import logging

# Turns logging on if you ever want it
logging.basicConfig(level=logging.INFO)

class Universe(object):

	''' A "universe" object that is used as a a middle man between whatever API ia used
		and the Wallet. The Universe objects starts a thread and constantly spins to update the
		fields of the dictionary. Then when anything wants the universe info it just calls the
		get method
	'''

	def __init__(self):
		self.universe_info = {}
		self.universe_info['btc_rate'] = 1
		self.universe_info['domestic_rate'] = 1
		self.universe_info['volume'] = 1

		a = threading.Thread(target=self.get_universe_info)
		a.setDaemon(True); a.start()

	def get_universe(self):
		''' Return the data to whatever wants it
			Returns the entire dictionary.
		'''

		return self.universe_info

	def get_universe_info(self):
		''' This method will be used to update the dictionary fields. The while loop
			spins indefinitely and will eventually update data at a certain rate.
		'''

		while True:
			pass
			sleep(1)

class Wallet(object):

	''' A Wallet object contains all the methods necessary to make a new wallet and
		compute its weight and then listen for new orders and convert upon receipt.
		When the wallet is initiated its initial coin value is normalized.
		One thread is starts in this class to loop through and detect new orders.
	'''

	def __init__(self, initial_order=0):

		self.universe = Universe()

		# All variables necessary for operation
		self.order_info = 0
		self.current_universe = 0
		self.exchange_rate = 0
		self.coins = 0
		self.current_volume = 0
		self.value = 0

		# Flag that is set on new order. Goes True when order is recieved and then goes
		# false after conversion is done.
		self.new_order = True

		# Thread to spin and listen for new orders
		a = threading.Thread(target=self.spin)
		a.setDaemon(True); a.start()

		# Get the current universe and normalize the original order
		self.current_universe = self.universe.get_universe()
		self.normalize(initial_order)

	def spin(self):
		''' Spins indefinitely to update universe and convert new orders when they arrive.
			Right now there is no way to get new orders so when the API is decided on,
			all it will have to do is find  way to flip the new_order variable and give the params
			to converter()
		'''
		# update universe
		self.current_universe = self.universe.get_universe()

		if self.new_order == True:
			# convert and then reset order flag
			self.converter(params=None)
			self.new_order = False

		sleep(1)

	def converter(self, params):
		''' This function follows the flowcharts on the datasheet provided.
			Because the universe is updated in the spin() fuynction there is no need
			to grab it here. Sub-methods are called at the bottom of this function
		'''

		# Dont know how params are coming in yet so these are dummy variables
		unpacked_params = params

		# Set order info as the params
		def order_info(order):
			self.order_info = order

		# get rates for universe
		def get_exhange_rate():
			self.domestic_ex_rate = self.current_universe['domestic_rate']
			self.btc_ex_rate = self.current_universe['btc_rate']

		# If the btc rate is more than the domestic rate then the final rate is 1
		# else is a ratio of the two rates
		def find_weakest_currency():
			if self.domestic_ex_rate < self.btc_ex_rate:
				self.final_rate = 1
			else:
				self.final_rate = 1/(self.domestic_ex_rate/self.btc_ex_rate)


		order_info(params)
		get_exhange_rate()
		find_weakest_currency()

	def normalize(self, initial_order=1):
		''' This function follows the flowcharts on the datasheet provided.
			Sub-methods are called at the bottom of this function
		'''

		# Dont know how params are coming in yet so these are dummy variables
		unpacked_params = initial_order

		# Add coins to the waller
		def add_coins_to_wallet(coins):
			self.coins = coins

		# Normalize the new wallet value as a function of its ration to the universe volume
		def normalize_wallet():
			self.current_volume = self.current_universe['volume']
			self.wallet_weight = self.coins / self.current_volume
			# Computer final value
			self.value = self.coins / self.wallet_weight

		add_coins_to_wallet(unpacked_params)
		normalize_wallet()

if __name__ == "__main__":

	# FOR TESTING - make a new wallet to test normalize and converter data flow
	wallet = Wallet(initial_order=1)

	# Loop until user exit
	while True:
		pass








